# YouTube Downloader & Transcriber

A Windows desktop app (CustomTkinter) to download audio (MP3), download video (MP4),
and transcribe videos to Markdown or PDF using [faster-whisper](https://github.com/SYSTRAN/faster-whisper).
Playlists are supported.

## Requirements
- Windows, Python 3.10+
- [ffmpeg](https://ffmpeg.org/) on `PATH` (MP3/MP4 merging and audio preparation)
- Optional: NVIDIA GPU for faster transcription (CUDA libraries are installed via pip; falls back to CPU automatically)

## Run
```
run.bat
```
On first run this creates `.venv` and installs `requirements.txt`. Or manually:
```
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python main.py
```

## Tests
```
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m pytest
```

## Docs
See `docs/` (PRD, tech stack, blueprint, task list).

## Disclaimer
For personal use only. Respect the terms of service of the sites you download from and the
copyright of the content. This project does not bypass any site protections.

## License
MIT, see [LICENSE](LICENSE).
