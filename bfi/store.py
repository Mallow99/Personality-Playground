"""Small, inspectable SQLite store. Only complete, successful exchanges are committed."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from bfi.errors import AppError

SCHEMA_VERSION = 1
SCHEMA = """
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
"""


def now():
    return datetime.now(UTC).isoformat()


def title_from(message):
    return " ".join(message.split())[:60]


class Store:
    """Every method opens its own connection, so any thread may call any method."""

    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version > SCHEMA_VERSION:
                # Refuse rather than guess: older code could damage a newer layout.
                raise AppError(
                    f"{path} was written by a newer version of this app (data format "
                    f"{version}; this version understands {SCHEMA_VERSION}). Update the app, "
                    "or point BFI_DATA_DIR at a different folder.",
                    "newer_data",
                )
            db.executescript(SCHEMA)
            db.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        try:
            with db:  # one transaction: commit on success, roll back on any exception
                yield db
        finally:
            db.close()

    @staticmethod
    def decode(row):
        data = dict(row)
        for key in ("character", "backend", "provenance"):
            if key in data and data[key]:
                data[key] = json.loads(data[key])
        return data

    def list(self):
        with self.connect() as db:
            rows = db.execute("SELECT * FROM conversations ORDER BY updated_at DESC, rowid DESC")
            return [self.decode(row) for row in rows]

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

    @staticmethod
    def _insert_exchange(db, cid, user, assistant, provenance, timestamp):
        db.execute(
            "INSERT INTO messages (conversation_id, role, content, created_at) "
            "VALUES (?, 'user', ?, ?)",
            (cid, user, timestamp),
        )
        db.execute(
            "INSERT INTO messages (conversation_id, role, content, created_at, provenance) "
            "VALUES (?, 'assistant', ?, ?, ?)",
            (cid, assistant, timestamp, json.dumps(provenance)),
        )

    def start(self, character, backend, user, assistant, provenance):
        """Create a conversation together with its first exchange, or create nothing."""
        cid, timestamp = str(uuid4()), now()
        with self.connect() as db:
            db.execute(
                "INSERT INTO conversations VALUES (?, ?, ?, ?, ?, ?)",
                (
                    cid,
                    title_from(user),
                    timestamp,
                    timestamp,
                    json.dumps(character),
                    json.dumps(backend),
                ),
            )
            self._insert_exchange(db, cid, user, assistant, provenance, timestamp)
        return self.get(cid)

    def append_exchange(self, cid, user, assistant, provenance):
        timestamp = now()
        with self.connect() as db:
            self._insert_exchange(db, cid, user, assistant, provenance, timestamp)
            # The title rule only matters for empty conversations saved by older versions.
            db.execute(
                "UPDATE conversations SET updated_at = ?, title = CASE "
                "WHEN title = 'New conversation' THEN ? ELSE title END WHERE id = ?",
                (timestamp, title_from(user), cid),
            )
        return self.get(cid)

    def delete(self, cid):
        with self.connect() as db:
            return db.execute("DELETE FROM conversations WHERE id = ?", (cid,)).rowcount > 0
