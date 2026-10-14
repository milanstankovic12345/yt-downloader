import tempfile
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from app import audio_prep, downloader, exporter
from app.screens.base import Screen
from app.transcriber import LANGUAGES, MODELS, transcribe

MEDIA_TYPES = [("Audio/Video", "*.mp3 *.m4a *.wav *.flac *.ogg *.opus *.mp4 *.mkv *.webm *.mov *.avi"),
               ("All files", "*.*")]
NO_FILE_TEXT = "Or use a local file: (none)"


class TranscribeScreen(Screen):
    button_text = "Transcribe"
    dir_key = "transcribe_dir"
    show_url_clear = False  # has its own Clear (URL + local file)

    def __init__(self, master, cfg):
        self.local_file: Path | None = None
        super().__init__(master, cfg)

    def _build_options(self, parent):
        parent.columnconfigure(0, weight=1)
        file_row = ctk.CTkFrame(parent, fg_color="transparent")
        file_row.grid(row=0, column=0, sticky="ew")
        file_row.columnconfigure(0, weight=1)
        self.file_lbl = ctk.CTkLabel(file_row, text=NO_FILE_TEXT, anchor="w")
        self.file_lbl.grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(file_row, text="Browse file", width=100, command=self._pick_file).grid(row=0, column=1, padx=4)
        ctk.CTkButton(file_row, text="Clear", width=60, fg_color="gray", command=self._clear_file).grid(row=0, column=2)

        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.grid(row=1, column=0, pady=(8, 0), sticky="ew")
        ctk.CTkLabel(row, text="Whisper model:").pack(side="left")
        self.model = ctk.CTkOptionMenu(row, values=MODELS, width=110)
        self.model.set(self.cfg["model"] if self.cfg["model"] in MODELS else "small")
        self.model.pack(side="left", padx=8)
        ctk.CTkLabel(row, text="Language:").pack(side="left", padx=(8, 0))
        self.language = ctk.CTkOptionMenu(row, values=list(LANGUAGES), width=110)
        self.language.set(self.cfg["language"] if self.cfg["language"] in LANGUAGES else "Auto")
        self.language.pack(side="left", padx=8)
        self.md_var = ctk.BooleanVar(value=self.cfg["markdown"])
        self.pdf_var = ctk.BooleanVar(value=self.cfg["pdf"])
        ctk.CTkCheckBox(row, text="Markdown", variable=self.md_var, width=20).pack(side="left", padx=8)
        ctk.CTkCheckBox(row, text="PDF", variable=self.pdf_var, width=20).pack(side="left", padx=8)

    def _pick_file(self):
        p = filedialog.askopenfilename(filetypes=MEDIA_TYPES)
        if p:
            self.local_file = Path(p)
            self.file_lbl.configure(text=f"Local file: {self.local_file.name}")

    def _clear_file(self):
        self.url.delete(0, "end")
        self.local_file = None
        self.file_lbl.configure(text=NO_FILE_TEXT)

    def _validate(self, url):
        if not url and not self.local_file:
            return "Paste a URL or choose a local file."
        if not (self.md_var.get() or self.pdf_var.get()):
            return "Tick Markdown and/or PDF."
        return None

    def _args(self):
        return (self.model.get(), self.md_var.get(), self.pdf_var.get(), self.local_file,
                LANGUAGES[self.language.get()])

    def collect_cfg(self):
        return {**super().collect_cfg(), "model": self.model.get(), "language": self.language.get(),
                "markdown": self.md_var.get(), "pdf": self.pdf_var.get()}

    def _run(self, url, out, model, md, pdf, local_file, language):
        with tempfile.TemporaryDirectory(prefix="yt-tool-") as tmp:
            tmp = Path(tmp)
            if local_file:
                src, title, source = local_file, local_file.stem, str(local_file)
            else:
                self._say("Downloading audio for transcription...")
                src, title = downloader.download_audio_raw(url, tmp, lambda v: self._prog(v * 0.2))
                source = url
            self._say("Preparing audio...")
            media = audio_prep.prepare(src, tmp, self._say)
            self._say("Transcribing...")
            t = transcribe(media, model, lambda v: self._prog(0.2 + v * 0.8), self._say, language)
        base = out / downloader.safe_name(title)
        saved = []
        if md:
            saved.append(exporter.write_markdown(t, title, source, base.with_suffix(".md")))
        if pdf:
            saved.append(exporter.write_pdf(t, title, source, base.with_suffix(".pdf")))
        for p in saved:
            self._say(f"Saved: {p}")
        return "Transcript saved:\n" + "\n".join(str(p) for p in saved)
