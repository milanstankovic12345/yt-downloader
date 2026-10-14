import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import parse_qs, urlparse

import yt_dlp

ProgressCb = Callable[[float], None]

AUDIO_QUALITIES = ["320 kbps", "192 kbps", "128 kbps"]
VIDEO_QUALITIES = ["Best", "1080p", "720p", "480p"]


def audio_bitrate(label: str) -> str:
    """'192 kbps' -> '192'; unknown labels fall back to the best (320)."""
    num = label.split()[0] if label else ""
    return num if num in ("128", "192", "320") else "320"


def video_format(label: str) -> str:
    """'720p' -> yt-dlp format capped at that height; 'Best' (or unknown) -> no cap."""
    if label in VIDEO_QUALITIES and label != "Best":
        h = label[:-1]
        return f"bestvideo*[height<={h}]+bestaudio/best[height<={h}]"
    return "bestvideo*+bestaudio/best"


@dataclass(frozen=True)
class PlaylistEntry:
    """One video in a playlist."""
    index: int
    id: str
    title: str
    url: str


def is_playlist_url(url: str) -> bool:
    """True for /playlist?list=... or a URL with list= but no v= (watch+list is a single video)."""
    try:
        u = urlparse(url.strip())
    except ValueError:
        return False
    q = parse_qs(u.query)
    if "list" not in q:
        return False
    return u.path.rstrip("/") == "/playlist" or "v" not in q


def parse_playlist(info: dict) -> tuple[str, list[PlaylistEntry]]:
    """Playlist info dict -> (title, entries); private/deleted/unavailable items are dropped."""
    entries = []
    for i, e in enumerate(info.get("entries") or [], 1):
        vid = (e or {}).get("id")
        title = (e or {}).get("title") or ""
        if not vid or title in ("[Private video]", "[Deleted video]"):
            continue
        entries.append(PlaylistEntry(i, vid, title or vid, f"https://www.youtube.com/watch?v={vid}"))
    return info.get("title") or "playlist", entries


def fetch_playlist(url: str) -> tuple[str, list[PlaylistEntry]]:
    """Fetch playlist title and entries (flat, no downloads). Blocks on the network."""
    opts = {"quiet": True, "no_warnings": True, "extract_flat": "in_playlist",
            "noplaylist": False, "skip_download": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        return parse_playlist(ydl.extract_info(url, download=False))


def item_prefix(index: int, total: int) -> str:
    """'03 - ' (zero-padded to the width of the playlist size, at least 2)."""
    return f"{index:0{max(2, len(str(total)))}d} - "


_BAD_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def safe_name(title: str, limit: int = 120) -> str:
    """Make a title safe to use as a Windows filename (non-ASCII is kept)."""
    name = _BAD_CHARS.sub("_", title).strip(" .")
    return (name or "untitled")[:limit]


def _outtmpl(out_dir: Path, prefix: str = "") -> str:
    return str(out_dir / (prefix.replace("%", "%%") + "%(title).120B.%(ext)s"))


def _hook(cb: ProgressCb | None):
    def hook(d):
        if cb and d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            if total:
                cb(min(d["downloaded_bytes"] / total, 1.0))
    return hook


def _run(url: str, opts: dict, cb: ProgressCb | None) -> dict:
    opts = {"quiet": True, "no_warnings": True, "noplaylist": True,
            "progress_hooks": [_hook(cb)], "windowsfilenames": True, **opts}
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=True)


def download_audio(url: str, out_dir: Path, cb: ProgressCb | None = None,
                   quality: str = "320 kbps", prefix: str = "") -> tuple[Path, str]:
    """Download audio as MP3 at the chosen bitrate. Returns (file path, title)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    info = _run(url, {
        "format": "bestaudio/best",
        "outtmpl": _outtmpl(out_dir, prefix),
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3",
                            "preferredquality": audio_bitrate(quality)}],
    }, cb)
    path = _final_path(info, ".mp3")
    return path, info.get("title", path.stem)


def download_audio_raw(url: str, out_dir: Path, cb: ProgressCb | None = None) -> tuple[Path, str]:
    """Download the original best audio stream (no lossy re-encode). Returns (file path, title)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    info = _run(url, {
        "format": "bestaudio/best",
        "outtmpl": str(out_dir / "%(title).120B.%(ext)s"),
    }, cb)
    path = _final_path(info, ".m4a")
    return path, info.get("title", path.stem)


def download_video(url: str, out_dir: Path, cb: ProgressCb | None = None,
                   quality: str = "Best", prefix: str = "") -> tuple[Path, str]:
    """Download video+audio merged as MP4, capped at the chosen height. Returns (file path, title)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    info = _run(url, {
        "format": video_format(quality),
        "merge_output_format": "mp4",
        "outtmpl": _outtmpl(out_dir, prefix),
    }, cb)
    path = _final_path(info, ".mp4")
    return path, info.get("title", path.stem)


def _final_path(info: dict, ext: str) -> Path:
    for item in info.get("requested_downloads") or []:
        fp = item.get("filepath")
        if fp:
            return Path(fp)
    return Path(info["_filename"]).with_suffix(ext)
