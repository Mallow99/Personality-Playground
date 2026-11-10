"""Small, inspectable SQLite store. Only complete, successful exchanges are committed."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


def now():
    return datetime.now(UTC).isoformat()


class Store:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY, title TEXT NOT NULL, created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL, character TEXT NOT NULL, backend TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY, conversation_id TEXT NOT NULL
                        REFERENCES conversations(id) ON DELETE CASCADE,
                    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')), content TEXT NOT NULL,
                    created_at TEXT NOT NULL, provenance TEXT
                );
                CREATE INDEX IF NOT EXISTS messages_conversation ON messages(conversation_id, id);
                PRAGMA user_version = 1;
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    def create(self, character, backend):
        cid, timestamp = str(uuid4()), now()
        with self.connect() as db:
            db.execute(
                "INSERT INTO conversations VALUES (?, ?, ?, ?, ?, ?)",
                (
                    cid,
                    "New conversation",
                    timestamp,
                    timestamp,
                    json.dumps(character),
                    json.dumps(backend),
                ),
            )
        return self.get(cid)

    def list(self):
        with self.connect() as db:
            rows = db.execute("SELECT * FROM conversations ORDER BY updated_at DESC, rowid DESC")
            return [self.decode(row) for row in rows]

    @staticmethod
    def decode(row):
        data = dict(row)
        for key in ("character", "backend", "provenance"):
            if key in data and data[key]:
                data[key] = json.loads(data[key])
        return data

    def get(self, cid):
        with self.connect() as db:
            row = db.execute("SELECT * FROM conversations WHERE id = ?", (cid,)).fetchone()
            if row is None:
                return None
            conversation = self.decode(row)
            conversation["messages"] = [
                self.decode(m)
                for m in db.execute(
                    "SELECT * FROM messages WHERE conversation_id = ? ORDER BY id", (cid,)
                )
            ]
            return conversation

    def append_exchange(self, cid, user, assistant, provenance):
        timestamp = now()
        with self.connect() as db:
            db.execute(
                "INSERT INTO messages (conversation_id, role, content, created_at) "
                "VALUES (?, 'user', ?, ?)",
                (cid, user, timestamp),
            )
            db.execute(
                "INSERT INTO messages "
                "(conversation_id, role, content, created_at, provenance) "
                "VALUES (?, 'assistant', ?, ?, ?)",
                (cid, assistant, timestamp, json.dumps(provenance)),
            )
            db.execute(
                "UPDATE conversations SET updated_at = ?, title = CASE "
                "WHEN title = 'New conversation' THEN ? ELSE title END WHERE id = ?",
                (timestamp, user[:60], cid),
            )
        return self.get(cid)

    def delete(self, cid):
        with self.connect() as db:
            return db.execute("DELETE FROM conversations WHERE id = ?", (cid,)).rowcount > 0
