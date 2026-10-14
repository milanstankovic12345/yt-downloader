import subprocess
import sys
from pathlib import Path
from typing import Callable

FILTERS = "highpass=f=80,loudnorm=I=-16:TP=-1.5:LRA=11"


def prepare(src: Path, dst_dir: Path, log: Callable[[str], None] | None = None) -> Path:
    """Convert to 16 kHz mono WAV with light cleanup. Returns `src` unchanged if ffmpeg fails."""
    dst = dst_dir / (src.stem + ".prep.wav")
    cmd = ["ffmpeg", "-y", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000",
           "-af", FILTERS, "-c:a", "pcm_s16le", str(dst)]
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    try:
        subprocess.run(cmd, check=True, capture_output=True, creationflags=flags)
        if dst.exists() and dst.stat().st_size > 0:
            return dst
    except (OSError, subprocess.SubprocessError) as e:
        if log:
            log(f"Audio cleanup skipped ({type(e).__name__}); using original audio.")
        return src
    if log:
        log("Audio cleanup produced no output; using original audio.")
    return src
