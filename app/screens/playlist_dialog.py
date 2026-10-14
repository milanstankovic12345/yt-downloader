from typing import Callable

import customtkinter as ctk

from app.downloader import PlaylistEntry


class PlaylistDialog(ctk.CTkToplevel):
    """Checklist of playlist items (all ticked). Calls on_confirm(selected) on OK; nothing on cancel."""

    def __init__(self, master, title: str, entries: list[PlaylistEntry],
                 on_confirm: Callable[[list[PlaylistEntry]], None]):
        super().__init__(master)
        self.title("Select videos")
        self.geometry("560x520")
        self.transient(master.winfo_toplevel())
        self._on_confirm = on_confirm
        self._entries = entries
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        ctk.CTkLabel(self, text=f"{title} ({len(entries)} videos)", anchor="w").grid(
            row=0, column=0, padx=16, pady=(16, 4), sticky="ew")
        box = ctk.CTkScrollableFrame(self)
        box.grid(row=1, column=0, padx=16, pady=4, sticky="nsew")
        self._vars: list[ctk.BooleanVar] = []
        for e in entries:
            var = ctk.BooleanVar(value=True)
            var.trace_add("write", lambda *_: self._refresh())
            self._vars.append(var)
            ctk.CTkCheckBox(box, text=f"{e.index}. {e.title}", variable=var).pack(anchor="w", pady=2)

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.grid(row=2, column=0, padx=16, pady=(4, 16), sticky="ew")
        ctk.CTkButton(row, text="Select all", width=90, fg_color="gray", command=lambda: self._set_all(True)).pack(side="left")
        ctk.CTkButton(row, text="Select none", width=90, fg_color="gray", command=lambda: self._set_all(False)).pack(side="left", padx=6)
        ctk.CTkButton(row, text="Cancel", width=80, fg_color="gray", command=self.destroy).pack(side="right")
        self.ok = ctk.CTkButton(row, text="", width=130, command=self._confirm)
        self.ok.pack(side="right", padx=6)
        self._refresh()
        self.after(100, self.grab_set)

    def _set_all(self, value: bool):
        for v in self._vars:
            v.set(value)

    def _refresh(self):
        n = sum(v.get() for v in self._vars)
        self.ok.configure(text=f"Download {n}", state="normal" if n else "disabled")

    def _confirm(self):
        selected = [e for e, v in zip(self._entries, self._vars) if v.get()]
        self.destroy()
        self._on_confirm(selected)
