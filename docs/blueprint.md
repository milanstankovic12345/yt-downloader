# Blueprint

```
main.py            entry point
app/settings.py    JSON config in %APPDATA%\yt-tool\config.json
app/downloader.py  yt-dlp wrapper: download_audio (MP3) / download_audio_raw / download_video
app/screens/playlist_dialog.py  checklist dialog for playlist items (UI only)
app/audio_prep.py  ffmpeg: 16 kHz mono WAV + highpass/loudnorm (falls back to original)
app/transcriber.py faster-whisper wrapper (language, beam 5, VAD, no prev-text conditioning) -> list[Segment]
app/exporter.py    Segment list -> .md / .pdf
app/ui.py          CustomTkinter window: left sidebar + three stacked screens
app/screens/       base.py (Screen: worker thread + queue, progress, log), audio.py, video.py, transcribe.py
tests/             pytest (settings, exporter, filename helpers)
```

Data flow (transcribe): URL → downloader.download_audio_raw (temp dir) → audio_prep (16 kHz mono WAV) → transcriber → exporter → `<transcribe folder>/<title>.md|pdf`. Temp files are deleted afterwards.
Data flow (playlist, Audio/Video): playlist URL → downloader.fetch_playlist (worker) → PlaylistDialog (main thread) → worker loops selected items → download_audio/video(prefix="NN - ") into `<dir>/<playlist title>/`; per-item errors are logged and skipped.
Local file: path → transcriber → exporter.

UI layout: left sidebar (Audio / Video / Transcribe). Each screen is fully separate: URL entry, its own options (audio quality | video quality | Whisper model, MD/PDF, local file), output folder (`audio_dir` / `video_dir` / `transcribe_dir`), action button, progress bar, log box.

Threading: each screen runs its action in a `threading.Thread`; workers push `("progress", float)`, `("log", str)`, `("done", ...)`, `("error", str)` to a `queue.Queue`; UI polls it with `after(100)`.
