# Tech stack

| Concern | Choice | Why |
|---|---|---|
| Language | Python 3.11+ | best ecosystem for yt-dlp and Whisper |
| GUI | customtkinter | modern look, pure Python (Answer: CustomTkinter) |
| Download | yt-dlp (pip) + ffmpeg on PATH | de-facto standard; ffmpeg merges and converts |
| Transcribe | faster-whisper | local, free, fast on CPU/GPU |
| GPU libs | nvidia-cublas-cu12, nvidia-cudnn-cu12 | faster-whisper (CTranslate2) needs cuBLAS 12 + cuDNN 9 DLLs for CUDA; without them it silently fell back to CPU. DLL folders registered at runtime in transcriber.py |
| Audio prep | ffmpeg (already required) | `audio_prep.py` converts to 16 kHz mono WAV with light cleanup before Whisper; no new dependency |
| PDF | fpdf2 + DejaVu font | Unicode support, no system deps |
| Tests | pytest (in requirements-dev.txt) | |

Launch: `run.bat` creates `.venv`, installs requirements, runs `main.py`.
