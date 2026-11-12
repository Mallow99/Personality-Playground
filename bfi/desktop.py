"""Native desktop window.

Threading rule: Tk widgets are touched only on the main thread. Anything slow (the model,
the database) runs on one worker thread at a time; the worker puts its outcome on a queue,
and `poll` picks it up on the main thread.
"""

import json
import queue
import threading
import tkinter as tk
import traceback
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

from bfi.errors import AppError
from bfi.service import ChatService

APP_NAME = "Best Friend Initiative"
IDLE_HINT = "Message (Ctrl+Enter to send)"
SENDING = "Waiting for the reply…"
POLL_MS = 50
_window = None


class DesktopApp:
    def __init__(self, root, service):
        self.root = root
        self.service = service
        self.config = service.config()
        self.current = None  # the open conversation, or None for an unsaved new one
        self.conversations = []
        self.busy = None  # label of the running task, or None when idle
        self.closed = False
        self.results = queue.Queue()
        root.title(APP_NAME)
        root.geometry("1000x700")
        root.minsize(640, 450)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(1, weight=1)
        root.protocol("WM_DELETE_WINDOW", self.close)

        self.mode = tk.StringVar()
        ttk.Label(root, textvariable=self.mode, padding=10).grid(
            row=0, column=0, columnspan=2, sticky="ew"
        )
        sidebar = ttk.Frame(root, padding=8)
        sidebar.grid(row=1, column=0, sticky="ns")
        sidebar.rowconfigure(1, weight=1)
        self.new_button = ttk.Button(sidebar, text="New conversation", command=self.new_chat)
        self.new_button.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.listbox = tk.Listbox(sidebar, width=28, exportselection=False)
        self.listbox.grid(row=1, column=0, sticky="nsew")
        self.listbox.bind("<<ListboxSelect>>", self.select_chat)
        self.export_button = ttk.Button(sidebar, text="Export JSON", command=self.export_chat)
        self.export_button.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        self.delete_button = ttk.Button(
            sidebar, text="Delete conversation", command=self.delete_chat
        )
        self.delete_button.grid(row=3, column=0, sticky="ew", pady=(4, 0))
        self.status_button = ttk.Button(sidebar, text="Check backend", command=self.check_status)
        self.status_button.grid(row=4, column=0, sticky="ew", pady=(12, 0))
        self.source_button = ttk.Button(sidebar, text="Reply source details", command=self.sources)
        self.source_button.grid(row=5, column=0, sticky="ew", pady=(4, 0))

        panel = ttk.Frame(root, padding=8)
        panel.grid(row=1, column=1, sticky="nsew")
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(1, weight=1)
        self.title = tk.StringVar(value="New conversation")
        ttk.Label(panel, textvariable=self.title, font=("TkDefaultFont", 15, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )
        self.transcript = scrolledtext.ScrolledText(panel, wrap="word", state="disabled")
        self.transcript.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.hint = tk.StringVar(value=IDLE_HINT)
        ttk.Label(panel, textvariable=self.hint).grid(row=2, column=0, sticky="w")
        self.draft = tk.Text(panel, height=4, wrap="word")
        self.draft.grid(row=3, column=0, sticky="ew", pady=(4, 0))
        self.draft.bind("<Control-Return>", self.send)
        self.send_button = ttk.Button(panel, text="Send", command=self.send)
        self.send_button.grid(row=3, column=1, padx=(8, 0), sticky="s")

        self.render()
        self.run_task("Loading conversations…", service.conversations, self.loaded)
        self.poll_timer = root.after(POLL_MS, self.poll)

    # --- Worker thread plumbing -------------------------------------------------------

    def run_task(self, label, operation, done):
        """Run `operation()` off the main thread, then call `done(result)` on the main thread."""
        if self.busy:
            return
        self.busy = label
        self.controls()

        def worker():
            try:
                outcome = (done, operation(), None)
            except Exception as exc:  # delivered to the main thread and shown there
                outcome = (done, None, exc)
            self.results.put(outcome)

        threading.Thread(target=worker, daemon=True).start()

    def poll(self):
        if self.closed:
            return
        try:
            while True:
                self.finish(*self.results.get_nowait())
        except queue.Empty:
            pass
        finally:
            # Reschedule even if a callback raised, or the window would stop responding
            # to finished work for the rest of the session.
            if not self.closed:
                self.poll_timer = self.root.after(POLL_MS, self.poll)

    def finish(self, done, result, error):
        self.busy = None
        self.controls()
        if error is None:
            done(result)
            return
        if isinstance(error, AppError):
            message = error.message
        else:
            traceback.print_exception(error)
            message = (
                f"Something unexpected went wrong ({type(error).__name__}: {error}).\n\n"
                "Your draft is kept. The full details were printed to the terminal."
            )
        self.show_error(message)
        if not self.closed:
            self.render()  # re-sync the list selection with the conversation actually open

    # --- Dialogs (separate methods so tests can replace them) ---------------------------

    def show_error(self, message):
        messagebox.showerror(APP_NAME, message, parent=self.root)

    def show_info(self, title, message):
        messagebox.showinfo(title, message, parent=self.root)

    def confirm(self, title, message):
        return messagebox.askyesno(title, message, parent=self.root)

    # --- Rendering ------------------------------------------------------------------------

    def controls(self):
        idle = not self.busy
        for widget in (
            self.new_button,
            self.listbox,
            self.status_button,
            self.send_button,
            self.draft,
        ):
            widget.configure(state="normal" if idle else "disabled")
        for widget in (self.export_button, self.delete_button, self.source_button):
            widget.configure(state="normal" if self.current and idle else "disabled")
        self.hint.set(self.busy or IDLE_HINT)

    def render(self):
        self.listbox.configure(state="normal")
        self.listbox.delete(0, tk.END)
        for index, conversation in enumerate(self.conversations):
            self.listbox.insert(tk.END, conversation["title"])
            if self.current and conversation["id"] == self.current["id"]:
                self.listbox.selection_set(index)
        self.title.set(self.current["title"] if self.current else "New conversation")
        if self.current and not self.service.can_continue(self.current):
            self.mode.set("Archived model configuration — start a new conversation to send.")
        elif self.config["backend"] == "mock":
            self.mode.set("Mock mode — scripted replies; no model inference.")
        else:
            self.mode.set(
                f"Local endpoint: {self.config['requested_model']} — history is sent to it."
            )
        self.transcript.configure(state="normal")
        self.transcript.delete("1.0", tk.END)
        if self.current:
            for msg in self.current["messages"]:
                name = "You" if msg["role"] == "user" else self.current["character"]["name"]
                self.transcript.insert(tk.END, f"{name}\n{msg['content']}\n\n")
        self.transcript.configure(state="disabled")
        self.transcript.see(tk.END)
        self.controls()

    # --- Actions. The draft is cleared only after a successful send. --------------------

    def loaded(self, conversations):
        self.conversations = conversations
        self.render()

    def new_chat(self):
        self.current = None
        self.render()
        self.draft.focus_set()

    def select_chat(self, _event=None):
        selected = self.listbox.curselection()
        if self.busy or not selected:
            return
        cid = self.conversations[selected[0]]["id"]
        if self.current and self.current["id"] == cid:
            return

        def done(conversation):
            self.current = conversation
            self.render()

        self.run_task("Opening conversation…", lambda: self.service.conversation(cid), done)

    def send(self, _event=None):
        content = self.draft.get("1.0", "end-1c").strip()
        if not content or self.busy:
            return "break"
        cid = self.current["id"] if self.current else None

        def done(conversation):
            self.current = conversation
            summary = {k: v for k, v in conversation.items() if k != "messages"}
            self.conversations = [summary] + [
                c for c in self.conversations if c["id"] != conversation["id"]
            ]
            self.draft.delete("1.0", tk.END)
            self.render()
            self.draft.focus_set()

        self.run_task(SENDING, lambda: self.service.send(cid, content), done)
        return "break"

    def delete_chat(self):
        if not self.current or not self.confirm(
            "Delete conversation", "Delete this conversation and all its messages?"
        ):
            return
        cid = self.current["id"]

        def done(_result):
            self.current = None
            self.conversations = [c for c in self.conversations if c["id"] != cid]
            self.render()

        self.run_task("Deleting…", lambda: self.service.delete(cid), done)

    def export_chat(self):
        if not self.current:
            return
        path = filedialog.asksaveasfilename(
            parent=self.root,
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialfile=f"bfi-{self.current['id']}.json",
        )
        if path:
            try:
                Path(path).write_text(
                    json.dumps(self.current, indent=2, ensure_ascii=False), encoding="utf-8"
                )
            except OSError as exc:
                self.show_error(f"Export failed: {exc}")

    def check_status(self):
        self.run_task(
            "Checking the backend…",
            self.service.status,
            lambda status: self.show_info(status["label"], status["detail"]),
        )

    def sources(self):
        if not self.current:
            return
        entries = [
            {"reply": i + 1, "source": msg["provenance"]}
            for i, msg in enumerate(m for m in self.current["messages"] if m.get("provenance"))
        ]
        window = tk.Toplevel(self.root)
        window.title("Reply source details")
        window.geometry("650x450")
        text = scrolledtext.ScrolledText(window, wrap="word")
        text.pack(fill="both", expand=True)
        text.insert(
            "1.0",
            json.dumps(entries, indent=2, ensure_ascii=False) if entries else "No replies yet.",
        )
        text.configure(state="disabled")

    def close(self):
        # Only complete exchanges are saved, so closing mid-reply discards the sent message.
        if self.busy == SENDING and not self.confirm(
            "A reply is still being generated",
            "If you close now, the message you just sent and its reply will not be saved.\n\n"
            "Close anyway?",
        ):
            return
        self.closed = True
        self.root.after_cancel(self.poll_timer)
        self.root.destroy()


def main():
    root = tk.Tk()
    root.withdraw()
    try:
        service = ChatService.from_env()
    except Exception as exc:
        if isinstance(exc, AppError):
            message = exc.message
        else:
            traceback.print_exc()
            message = f"{type(exc).__name__}: {exc}"
        messagebox.showerror(APP_NAME, f"The app could not start.\n\n{message}")
        root.destroy()
        return 1
    # Kept in a module global so the window is never garbage-collected before the process
    # exits: Tcl aborts if that happens on the worker thread, which may still be running.
    global _window
    _window = DesktopApp(root, service)
    root.deiconify()
    root.mainloop()
    return 0
