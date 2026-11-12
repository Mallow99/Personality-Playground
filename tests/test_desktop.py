"""The real Tk window, driven on a real (or virtual) display with a controllable backend.

Without Tk or a display these tests skip. Set BFI_REQUIRE_TK=1 (CI does) to fail instead.
"""

import gc
import os
import threading
import time

import pytest

from bfi.backends import BackendError, MockBackend
from bfi.errors import AppError
from bfi.service import ChatService

REQUIRE_TK = bool(os.getenv("BFI_REQUIRE_TK"))
if REQUIRE_TK:
    import tkinter as tk
else:
    tk = pytest.importorskip("tkinter")

from bfi import desktop  # noqa: E402  (needs tkinter)


class GateBackend(MockBackend):
    """Holds a reply until released, and can be told to fail."""

    def __init__(self):
        self.entered, self.release, self.fail = threading.Event(), threading.Event(), False
        self.release.set()

    def complete(self, messages):
        self.entered.set()
        assert self.release.wait(5)
        if self.fail:
            raise BackendError("Server unavailable", "connection")
        return super().complete(messages)


def pump(app, until, timeout=5):
    """Run the Tk event loop until `until()` is true, as mainloop would."""
    deadline = time.monotonic() + timeout
    while not until():
        assert time.monotonic() < deadline, "the window did not reach the expected state"
        app.root.update()
        time.sleep(0.005)


def idle(app):
    return lambda: not app.busy


def make_root():
    try:
        return tk.Tk()
    except tk.TclError as exc:
        if REQUIRE_TK:
            raise
        pytest.skip(f"No display for Tk: {exc}")


@pytest.fixture(autouse=True)
def tk_objects_die_on_the_main_thread():
    """Tcl aborts the process if an old Tk interpreter is garbage-collected on a worker
    thread, so collect leftovers here, on the main thread, around every test."""
    gc.collect()
    yield
    gc.collect()


@pytest.fixture
def app(settings):
    root = make_root()
    backend = GateBackend()
    window = desktop.DesktopApp(root, ChatService(settings, backend))
    window.backend, window.errors, window.answers = backend, [], []
    window.show_error = window.errors.append
    window.confirm = lambda *_: window.answers.pop(0)
    pump(window, idle(window))
    yield window
    backend.release.set()
    if not window.closed:
        pump(window, idle(window))
        root.destroy()


def write(app, text):
    app.draft.insert("1.0", text)


def draft(app):
    return app.draft.get("1.0", "end-1c")


def test_successful_send_saves_renders_and_clears_the_draft(app):
    write(app, "Hello there")
    app.send()
    pump(app, idle(app))
    assert draft(app) == "" and app.errors == []
    assert "Hello there" in app.transcript.get("1.0", "end")
    assert "no model inference" in app.transcript.get("1.0", "end")
    assert app.listbox.get(0, "end") == ("Hello there",)
    assert app.listbox.curselection() == (0,)
    assert [c["title"] for c in app.service.conversations()] == ["Hello there"]


def test_failed_send_keeps_draft_and_retry_creates_exactly_one_conversation(app):
    app.backend.fail = True
    write(app, "Important draft")
    app.send()
    pump(app, idle(app))
    assert app.errors == ["Server unavailable"]
    assert draft(app) == "Important draft"
    assert str(app.draft.cget("state")) == "normal"
    assert app.current is None and app.service.conversations() == []
    app.backend.fail = False
    app.send()
    pump(app, idle(app))
    assert draft(app) == ""
    assert len(app.service.conversations()) == 1 and app.listbox.size() == 1


def test_controls_lock_while_generating_and_closing_asks_first(app):
    app.backend.release.clear()
    write(app, "Slow question")
    app.send()
    pump(app, app.backend.entered.is_set)
    assert app.hint.get() == desktop.SENDING
    for widget in (app.send_button, app.draft, app.listbox, app.new_button):
        assert str(widget.cget("state")) == "disabled"
    app.send()  # a second send while busy is ignored, not queued
    app.answers.append(False)
    app.close()
    assert not app.closed and app.answers == []
    app.backend.release.set()
    pump(app, idle(app))
    assert app.hint.get() == desktop.IDLE_HINT
    assert len(app.service.conversations()) == 1
    assert len(app.current["messages"]) == 2


def test_confirmed_close_during_generation_saves_nothing_partial(app):
    app.backend.release.clear()
    write(app, "Never finished")
    app.send()
    pump(app, app.backend.entered.is_set)
    app.answers.append(True)
    app.close()
    assert app.closed
    app.poll()  # a late timer tick after closing must not touch destroyed widgets
    assert app.service.conversations() == []


def test_idle_close_does_not_ask(app):
    app.close()
    assert app.closed and app.answers == []


def test_switching_conversations_never_discards_the_draft(app):
    for text in ("First chat", "Second chat"):
        app.new_chat()
        write(app, text)
        app.send()
        pump(app, idle(app))
    write(app, "Unsent thought")
    app.listbox.selection_clear(0, "end")
    app.listbox.selection_set(1)
    app.select_chat()
    pump(app, idle(app))
    assert app.current["title"] == "First chat"
    assert draft(app) == "Unsent thought"
    app.new_chat()
    assert app.current is None and draft(app) == "Unsent thought"


def test_delete_asks_first_and_removes_the_conversation(app):
    write(app, "Disposable")
    app.send()
    pump(app, idle(app))
    app.answers.append(False)
    app.delete_chat()
    assert len(app.service.conversations()) == 1
    app.answers.append(True)
    app.delete_chat()
    pump(app, idle(app))
    assert app.current is None and app.listbox.size() == 0
    assert app.service.conversations() == []


def test_archived_conversation_is_labelled_and_send_explains(app, settings):
    write(app, "Mock era")
    app.send()
    pump(app, idle(app))
    app.service.settings = type(settings)(
        backend="openai", data_dir=settings.data_dir, character_file=settings.character_file
    )
    app.render()
    assert app.mode.get().startswith("Archived model configuration")
    write(app, "Continue?")
    app.send()
    pump(app, idle(app))
    assert "different backend or model" in app.errors[0]
    assert draft(app) == "Continue?"


def test_unexpected_errors_are_reported_and_the_window_keeps_working(app, capsys):
    def explode():
        raise KeyError("label")

    app.run_task("Testing…", explode, lambda _: None)
    pump(app, idle(app))
    assert "Something unexpected went wrong (KeyError" in app.errors[0]
    assert "KeyError" in capsys.readouterr().err

    reported = []
    app.root.report_callback_exception = lambda *exc: reported.append(exc)
    app.run_task("Testing…", lambda: 1, lambda _: 1 / 0)  # a bug inside a UI callback
    pump(app, lambda: reported)
    write(app, "Still alive")
    app.send()
    pump(app, idle(app))
    assert draft(app) == "" and len(app.service.conversations()) == 1


def test_startup_problem_is_shown_instead_of_a_bare_traceback(monkeypatch):
    shown = []

    def broken():
        raise AppError("BFI_BACKEND must be mock or openai.", "config")

    monkeypatch.setattr(desktop.ChatService, "from_env", staticmethod(broken))
    monkeypatch.setattr(desktop.messagebox, "showerror", lambda *args, **_: shown.append(args))
    make_root().destroy()  # skips here when there is no display
    assert desktop.main() == 1
    assert "BFI_BACKEND must be mock or openai." in shown[0][1]
