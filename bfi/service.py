"""The application itself: every rule about conversations lives here, with no UI and no HTTP.

The desktop window calls these methods directly. They block, so the window runs them on a
worker thread. Expected failures raise AppError with a message meant for the user.
"""

import threading
import time

from dotenv import load_dotenv

from bfi.backends import MockBackend, OpenAIBackend
from bfi.config import ROOT, Settings, load_character
from bfi.errors import AppError
from bfi.store import Store

MAX_MESSAGE_CHARS = 8000


def context_for(conversation, content, settings):
    """Send recent complete pairs; the full transcript remains in SQLite."""
    prompt = conversation["character"]["system_prompt"]
    budget = settings.context_chars - len(prompt) - len(content)
    selected = []
    history = conversation["messages"]
    for end in range(len(history), max(0, len(history) - settings.history_pairs * 2), -2):
        pair = history[end - 2 : end]
        cost = sum(len(m["content"]) for m in pair)
        if cost > budget:
            break
        selected = [{"role": m["role"], "content": m["content"]} for m in pair] + selected
        budget -= cost
    return (
        [{"role": "system", "content": prompt}] + selected + [{"role": "user", "content": content}],
        len(history) - len(selected),
    )


class ChatService:
    def __init__(self, settings: Settings, backend=None):
        self.settings = settings
        self.character = load_character(settings.character_file)
        self.store = Store(settings.data_dir / "conversations.sqlite3")
        self.backend = backend or (
            MockBackend() if settings.backend == "mock" else OpenAIBackend(settings)
        )
        # One generation at a time suits a single GPU and keeps transcript order deterministic.
        self._generating = threading.Lock()

    @classmethod
    def from_env(cls):
        load_dotenv(ROOT / ".env")
        return cls(Settings.from_env())

    def config(self):
        return {
            **self.settings.identity,
            "character": self.character,
            "history_pairs": self.settings.history_pairs,
            "context_chars": self.settings.context_chars,
        }

    def status(self):
        return {**self.settings.identity, **self.backend.status()}

    def conversations(self):
        return self.store.list()

    def conversation(self, cid):
        conversation = self.store.get(cid)
        if conversation is None:
            raise AppError("Conversation not found.", "not_found")
        return conversation

    def can_continue(self, conversation):
        """Old chats stay readable, but never mix history from different backends or models."""
        return conversation["backend"] == self.settings.identity

    def send(self, cid, content):
        """Generate a reply and save the exchange. `cid=None` starts a new conversation.

        Nothing is written unless generation succeeds: a failed first message leaves no
        empty conversation behind, and a failed later message leaves the transcript as it was.
        """
        content = content.strip()
        if not content:
            raise AppError("Write a message before sending.", "invalid")
        if len(content) > MAX_MESSAGE_CHARS:
            raise AppError(
                f"This message has {len(content)} characters; the limit is {MAX_MESSAGE_CHARS}.",
                "invalid",
            )
        if not self._generating.acquire(blocking=False):
            raise AppError("A reply is already being generated. Wait and try again.", "busy")
        try:
            if cid is None:
                conversation = {
                    "character": self.character,
                    "backend": self.settings.identity,
                    "messages": [],
                }
            else:
                conversation = self.conversation(cid)
            if not self.can_continue(conversation):
                raise AppError(
                    "This conversation uses a different backend or model. "
                    "Start a new conversation to keep its history separate.",
                    "archived",
                )
            messages, omitted = context_for(conversation, content, self.settings)
            if sum(len(m["content"]) for m in messages) > self.settings.context_chars:
                raise AppError(
                    "The character prompt and message exceed BFI_CONTEXT_CHARS. "
                    "Shorten the message or raise that setting.",
                    "invalid",
                )
            started = time.perf_counter()
            result = self.backend.complete(messages)
            provenance = {
                **self.settings.identity,
                "reported_model": result["reported_model"],
                "cloud_assistance": "none_by_app",
                "endpoint_locality": "mock"
                if self.settings.backend == "mock"
                else "unverified_loopback",
                "elapsed_ms": round((time.perf_counter() - started) * 1000),
                "usage": result["usage"],
                "context_messages_omitted": omitted,
            }
            if cid is None:
                return self.store.start(
                    conversation["character"],
                    conversation["backend"],
                    content,
                    result["content"],
                    provenance,
                )
            return self.store.append_exchange(cid, content, result["content"], provenance)
        finally:
            self._generating.release()

    def delete(self, cid):
        if not self._generating.acquire(blocking=False):
            raise AppError("Wait for the current reply before deleting.", "busy")
        try:
            if not self.store.delete(cid):
                raise AppError("Conversation not found.", "not_found")
        finally:
            self._generating.release()
