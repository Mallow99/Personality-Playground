"""Single-resource generation queue with durable status and explicit cancellation.

Interrupted work is never automatically replayed: a tool may already have run.
"""

import asyncio
import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from bfi.store import now

TERMINAL = {"succeeded", "failed", "cancelled", "interrupted"}


class QueueFull(ValueError):
    pass


class JobManager:
    def __init__(self, path: Path, execute, limit=16):
        self.path, self.execute, self.limit = path, execute, limit
        self.tasks, self.live = {}, {}
        self.gate = asyncio.Semaphore(1)
        self.closing = False
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL,
                    request_id TEXT UNIQUE, payload TEXT NOT NULL, state TEXT NOT NULL,
                    partial TEXT NOT NULL DEFAULT '', error TEXT, result TEXT,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
            """)
            db.execute(
                "UPDATE jobs SET state='interrupted', error=?, updated_at=? "
                "WHERE state IN ('queued','running')",
                ("The handler restarted. Inspect the conversation before submitting again.", now()),
            )

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def get(self, jid):
        with self.connect() as db:
            row = db.execute("SELECT * FROM jobs WHERE id=?", (jid,)).fetchone()
        if not row:
            return None
        job = dict(row)
        job["input_content"] = json.loads(job.pop("payload"))["content"]
        job["result"] = json.loads(job["result"]) if job["result"] else None
        if jid in self.live:
            job["partial"] = self.live[jid]
        return job

    def list(self, cid=None):
        with self.connect() as db:
            if cid:
                ids = db.execute(
                    "SELECT id FROM jobs WHERE conversation_id=? ORDER BY created_at DESC LIMIT 50",
                    (cid,),
                ).fetchall()
            else:
                ids = db.execute("SELECT id FROM jobs ORDER BY created_at DESC LIMIT 50").fetchall()
        return [self.get(row["id"]) for row in ids]

    def has_pending(self):
        with self.connect() as db:
            return (
                db.execute(
                    "SELECT 1 FROM jobs WHERE state IN ('queued','running') LIMIT 1"
                ).fetchone()
                is not None
            )

    def update(self, jid, **values):
        values["updated_at"] = now()
        # Column names are internal constants, never request data.
        with self.connect() as db:
            db.execute(
                "UPDATE jobs SET " + ",".join(f"{key}=?" for key in values) + " WHERE id=?",
                [*values.values(), jid],
            )

    def submit(self, cid, payload, request_id=None):
        if self.closing:
            raise QueueFull("The handler is shutting down. Restart it before submitting work.")
        encoded = json.dumps(payload, sort_keys=True)
        with self.connect() as db:
            if request_id:
                previous = db.execute(
                    "SELECT id,conversation_id,payload FROM jobs WHERE request_id=?", (request_id,)
                ).fetchone()
                if previous:
                    if previous["conversation_id"] != cid or previous["payload"] != encoded:
                        raise ValueError("This request ID already belongs to a different message.")
                    return self.get(previous["id"])
            count = db.execute(
                "SELECT count(*) FROM jobs WHERE state IN ('queued','running')"
            ).fetchone()[0]
            if count >= self.limit:
                raise QueueFull("The generation queue is full. Wait or cancel a pending request.")
            jid, timestamp = str(uuid4()), now()
            db.execute(
                "INSERT INTO jobs "
                "(id,conversation_id,request_id,payload,state,created_at,updated_at) "
                "VALUES (?,?,?,?,'queued',?,?)",
                (jid, cid, request_id, encoded, timestamp, timestamp),
            )
        task = asyncio.create_task(self.run(jid, cid, payload), name=f"bfi-job-{jid}")
        self.tasks[jid] = task
        task.add_done_callback(lambda _: self.tasks.pop(jid, None))
        return self.get(jid)

    async def run(self, jid, cid, payload):
        last_flush = 0

        def on_delta(delta):
            nonlocal last_flush
            self.live[jid] = (self.live.get(jid, "") + delta)[:160000]
            clock = time.monotonic()
            if clock - last_flush >= 0.15:
                self.update(jid, partial=self.live[jid])
                last_flush = clock

        try:
            async with self.gate:
                if self.get(jid)["state"] != "queued":
                    return
                self.update(jid, state="running")
                result = await self.execute(cid, payload, on_delta)
                self.update(
                    jid,
                    state="succeeded",
                    partial=result["messages"][-1]["content"],
                    result=json.dumps(
                        {
                            "conversation_id": cid,
                            "assistant_message_id": result["messages"][-1]["id"],
                        }
                    ),
                )
        except asyncio.CancelledError:
            if self.get(jid)["state"] not in TERMINAL:
                self.update(
                    jid,
                    state="interrupted" if self.closing else "cancelled",
                    partial=self.live.get(jid, ""),
                    error="Handler stopped; work was not replayed." if self.closing else None,
                )
            raise
        except Exception as exc:
            from fastapi import HTTPException

            from bfi.backends import BackendError

            detail = (
                exc.message
                if isinstance(exc, BackendError)
                else (
                    exc.detail
                    if isinstance(exc, HTTPException) and isinstance(exc.detail, str)
                    else "The handler could not complete this request. No reply was saved."
                )
            )
            self.update(jid, state="failed", error=detail, partial=self.live.get(jid, ""))
        finally:
            self.live.pop(jid, None)

    async def cancel(self, jid):
        job = self.get(jid)
        if not job:
            return None
        if job["state"] not in TERMINAL:
            task = self.tasks.get(jid)
            if task:
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
            if self.get(jid)["state"] not in TERMINAL:
                self.update(jid, state="cancelled")
        return self.get(jid)

    async def shutdown(self):
        self.closing = True
        tasks = list(self.tasks.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        with self.connect() as db:
            db.execute(
                "UPDATE jobs SET state='interrupted', error=?, updated_at=? "
                "WHERE state IN ('queued','running')",
                ("Handler stopped; work was not replayed.", now()),
            )

    async def delete_conversation(self, cid):
        with self.connect() as db:
            ids = [r[0] for r in db.execute("SELECT id FROM jobs WHERE conversation_id=?", (cid,))]
        for jid in ids:
            await self.cancel(jid)
        with self.connect() as db:
            db.execute("DELETE FROM jobs WHERE conversation_id=?", (cid,))
