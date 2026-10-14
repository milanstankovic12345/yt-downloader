# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# YouTube Downloader & Transcriber

Personal Windows desktop app (CustomTkinter): download audio (MP3), download video (MP4), transcribe (faster-whisper) to Markdown/PDF.

## Commands
- Run: `run.bat` (creates `.venv` and installs `requirements.txt` on first run) or `.venv\Scripts\python main.py`
- Test all (first `pip install -r requirements-dev.txt`): `.venv\Scripts\python -m pytest`
- Single test: `.venv\Scripts\python -m pytest tests/test_core.py::test_safe_name`
- No linter or build step is configured. `ffmpeg` must be on PATH (used by yt-dlp for MP3/MP4 merging and by `audio_prep`).

## Docs
`docs/prd.md`, `docs/techstack.md`, `docs/blueprint.md` (module map and data flows), `docs/tasks.md` (task checklist; tick items when done), `docs/kickstart/answers.md`. Update `blueprint.md` when module boundaries or data flow change. `.claude/agents/` defines builder, tester and reviewer agents that work from `docs/tasks.md`.

## Architecture
- `app/ui.py` builds the window: left sidebar plus three independent screens (Audio / Video / Transcribe) in `app/screens/`. `screens/base.py` holds the shared `Screen` class: worker thread, progress bar, log box, and the playlist flow.
- Worker-to-UI communication: workers push `("progress", float)`, `("log", str)`, `("done", ...)` and `("error", str)` onto a `queue.Queue`. The UI polls it with `after(100)`. Follow this pattern for any new background work.
- Core modules (`downloader`, `audio_prep`, `transcriber`, `exporter`, `settings`) are UI-free and take plain callbacks (`ProgressCb`, `log`).
- Transcribe pipeline: `downloader.download_audio_raw` into a temp dir, then `audio_prep.prepare` (ffmpeg to 16 kHz mono WAV, returns the original file if ffmpeg fails), then `transcriber` (returns `Transcript` of `Segment`s), then `exporter.write_markdown` / `write_pdf`. Temp files are deleted afterwards.
- Playlists: `fetch_playlist` runs in a worker, `PlaylistDialog` runs on the main thread, then the worker loops over the selected items. Per-item errors are logged and skipped. Output goes to `<dir>/<playlist title>/` with an `item_prefix` like `NN - `.
- Settings are JSON at `%APPDATA%\yt-tool\config.json` (`settings.load`/`save`); each screen has its own output dir (`audio_dir` / `video_dir` / `transcribe_dir`) defaulting from `output_dir`.

## Gotchas
- `transcriber.py` keeps module-level state: a model cache keyed by `(model, device)` and a `_cuda_broken` flag. Once the GPU fails, every later run stays on CPU/int8 until restart. Tests monkeypatch this state.
- CUDA on Windows works through the pip `nvidia-cublas-cu12` / `nvidia-cudnn-cu12` packages. `_register_cuda_dlls` adds their `bin` dirs to the DLL search path and `PATH`.
- `exporter.write_pdf` needs a Unicode TTF (Arial or Segoe UI from `%WINDIR%\Fonts`). Without one it falls back to Helvetica with latin-1 replacement, so non-ASCII text is lossy.
- Tests are in a single file, `tests/test_core.py`, and cover pure logic with monkeypatching. Nothing hits the network or runs real Whisper or ffmpeg.

## Rules
- Keep modules small as in blueprint; no UI code in downloader/transcriber/exporter.
- Long work only in worker threads; never touch widgets off the main thread.
- Sanitize filenames (`downloader.safe_name`); support non-ASCII titles.
- No new dependencies without a reason in docs/techstack.md.
- Personal use only; do not add bypasses of site protections.
