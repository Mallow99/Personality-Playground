"""Native desktop interface. The application API runs in-process, without a web server."""

import asyncio
import json
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

import httpx

from bfi.main import create_app


class DesktopApp:
    def __init__(self, root, app=None):
        self.root = root
        self.app = app or create_app()
        self.current = None
        self.conversations = []
        self.busy = False
        self.results = queue.Queue()
        root.title("Best Friend Initiative")
        root.geometry("1000x700")
        root.minsize(640, 450)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(1, weight=1)

        self.mode = tk.StringVar(value="Loading configuration…")
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
        ttk.Label(panel, text="Message (Ctrl+Enter to send)").grid(row=2, column=0, sticky="w")
        self.draft = tk.Text(panel, height=4, wrap="word")
        self.draft.grid(row=3, column=0, sticky="ew", pady=(4, 0))
        self.draft.bind("<Control-Return>", self.send)
        self.send_button = ttk.Button(panel, text="Send", command=self.send)
        self.send_button.grid(row=3, column=1, padx=(8, 0), sticky="s")
        self.config = None
        self.run_task(self.initialize, self.initialized)
        root.after(50, self.poll)

    async def request(self, method, path, **kwargs):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=self.app), base_url="http://localhost"
        ) as client:
            response = await client.request(method, "/api" + path, **kwargs)
        if response.is_error:
            detail = response.json().get("detail", "Request failed.")
            raise RuntimeError(detail if isinstance(detail, str) else "Invalid request.")
        return None if response.status_code == 204 else response.json()

    def run_task(self, operation, callback):
        if self.busy:
            return
        self.busy = True
        self.controls()

        def worker():
            try:
                self.results.put((callback, asyncio.run(operation()), None))
            except Exception as exc:
                self.results.put((callback, None, exc))

        threading.Thread(target=worker, daemon=True).start()

    def poll(self):
        try:
            while True:
                callback, result, error = self.results.get_nowait()
                self.busy = False
                self.controls()
                if error:
                    messagebox.showerror("Best Friend Initiative", str(error), parent=self.root)
                else:
                    callback(result)
                self.controls()
        except queue.Empty:
            pass
        self.root.after(50, self.poll)

    def controls(self):
        state = "disabled" if self.busy else "normal"
        for widget in (
            self.new_button,
            self.listbox,
            self.status_button,
            self.send_button,
            self.draft,
        ):
            widget.configure(state=state)
        for widget in (self.export_button, self.delete_button, self.source_button):
            widget.configure(state="normal" if self.current and not self.busy else "disabled")

    async def initialize(self):
        return await self.request("GET", "/config"), await self.request("GET", "/conversations")

    def initialized(self, result):
        self.config, self.conversations = result
        self.render()

    def render(self):
        self.listbox.delete(0, tk.END)
        for index, conversation in enumerate(self.conversations):
            self.listbox.insert(tk.END, conversation["title"])
            if self.current and conversation["id"] == self.current["id"]:
                self.listbox.selection_set(index)
        self.title.set(self.current["title"] if self.current else "New conversation")
        if self.current and self.current["backend"] != {
            key: self.config[key] for key in ("backend", "endpoint", "requested_model")
        }:
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

    def new_chat(self):
        self.current = None
        self.draft.delete("1.0", tk.END)
        self.render()
        self.draft.focus_set()

    def select_chat(self, _event):
        selected = self.listbox.curselection()
        if self.busy or not selected:
            return
        cid = self.conversations[selected[0]]["id"]
        if self.current and self.current["id"] == cid:
            return

        async def operation():
            return await self.request("GET", f"/conversations/{cid}")

        def done(conversation):
            self.current = conversation
            self.draft.delete("1.0", tk.END)
            self.render()

        self.run_task(operation, done)

    def send(self, _event=None):
        content = self.draft.get("1.0", "end-1c").strip()
        if not content or self.busy:
            return "break"
        cid = self.current["id"] if self.current else None

        async def operation():
            nonlocal cid
            if cid is None:
                conversation = await self.request("POST", "/conversations")
                cid = conversation["id"]
            conversation = await self.request(
                "POST", f"/conversations/{cid}/messages", json={"content": content}
            )
            return conversation, await self.request("GET", "/conversations")

        def done(result):
            self.current, self.conversations = result
            self.draft.delete("1.0", tk.END)
            self.render()
            self.draft.focus_set()

        self.run_task(operation, done)
        return "break"

    def delete_chat(self):
        if not self.current or not messagebox.askyesno(
            "Delete conversation",
            "Delete this conversation and all its messages?",
            parent=self.root,
        ):
            return
        cid = self.current["id"]

        async def operation():
            await self.request("DELETE", f"/conversations/{cid}")
            return await self.request("GET", "/conversations")

        def done(conversations):
            self.current = None
            self.conversations = conversations
            self.render()

        self.run_task(operation, done)

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
                messagebox.showerror("Export failed", str(exc), parent=self.root)

    def check_status(self):
        async def operation():
            return await self.request("GET", "/status")

        self.run_task(
            operation,
            lambda status: messagebox.showinfo(status["label"], status["detail"], parent=self.root),
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


def main():
    root = tk.Tk()
    DesktopApp(root)
    root.mainloop()
