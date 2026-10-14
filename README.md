# YouTube Downloader & Transcriber

A Windows desktop app (CustomTkinter) to download audio (MP3), download video (MP4),
and transcribe videos to Markdown or PDF using [faster-whisper](https://github.com/SYSTRAN/faster-whisper).
Playlists are supported.

## Requirements
- Windows, Python 3.10+
- [ffmpeg](https://ffmpeg.org/) on `PATH` (MP3/MP4 merging and audio preparation)
- Optional: NVIDIA GPU for faster transcription (CUDA libraries are installed via pip; falls back to CPU automatically)

## Get it on another PC
```
git clone https://github.com/milanstankovic12345/yt-downloader.git
cd yt-downloader
```
No git? Use **Code -> Download ZIP** on the GitHub page and unzip it. Install Python 3.10+ and ffmpeg first.

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

## Disclaimer
For personal use only. Respect the terms of service of the sites you download from and the
copyright of the content. This project does not bypass any site protections.

## License
MIT, see [LICENSE](LICENSE).
