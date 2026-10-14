# PRD — YouTube Downloader & Transcriber

Personal-use Windows desktop app (V1 archetype: personal tool; single user).

## Goal
One window, three actions:
1. **Download audio** from a YouTube URL → MP3.
2. **Download video** from a YouTube URL → MP4 (best quality).
3. **Transcribe** a YouTube URL or a local audio/video file → Markdown and/or PDF.

## Requirements
- Folder picker for output; last choice remembered. Subfolders `audio/`, `video/`, `transcripts/`.
- Transcription is local (faster-whisper); model selectable (tiny…large-v3), default `small`; GPU used when available; language auto-detected.
- Playlists (Audio/Video screens): a playlist URL is detected, items are listed in a checklist (all ticked), each selected item is saved as a separate file in `<folder>/<playlist title>/NN - <title>.ext`; a failing item is skipped and reported at the end. A watch URL with both `v=` and `list=` is treated as a single video.
- Progress bar + log; UI never freezes; readable errors.
- Transcript files contain title, source, date, language, timestamped text.

## Out of scope (v1)
Login/cookies, SRT export, cloud APIs, playlists in Transcribe. [ASSUMPTION]

## Constraints
Personal use only; user is responsible for respecting YouTube ToS and copyright.
