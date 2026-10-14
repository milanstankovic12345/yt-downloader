import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

MODELS = ["tiny", "base", "small", "medium", "large-v3"]

# label -> ISO code for Whisper; None = auto-detect
LANGUAGES = {"Auto": None, "English": "en", "Serbian": "sr", "Croatian": "hr", "Bosnian": "bs",
             "German": "de", "French": "fr", "Spanish": "es", "Italian": "it", "Russian": "ru",
             "Portuguese": "pt", "Dutch": "nl", "Polish": "pl", "Turkish": "tr"}


@dataclass
class Segment:
    """A timed piece of transcribed text."""
    start: float
    end: float
    text: str


@dataclass
class Transcript:
    """Full transcript: segments plus the detected language."""
    segments: list[Segment]
    language: str


_models: dict = {}       # (model, device) -> loaded WhisperModel, reused between runs
_cuda_broken = False     # set after a GPU failure so later runs go straight to CPU
_dlls_done = False


def _register_cuda_dlls() -> None:
    """Make pip-installed nvidia-* DLLs (cublas, cudnn) findable on Windows."""
    global _dlls_done
    if _dlls_done:
        return
    _dlls_done = True
    for base in sys.path:
        nv = Path(base) / "nvidia"
        if not nv.is_dir():
            continue
        for bin_dir in nv.glob("*/bin"):
            try:
                os.add_dll_directory(str(bin_dir))
            except (OSError, AttributeError):
                pass
            os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")


def _device() -> tuple[str, str]:
    if _cuda_broken:
        return "cpu", "int8"
    try:
        _register_cuda_dlls()
        import ctranslate2
        if ctranslate2.get_cuda_device_count() > 0:
            return "cuda", "float16"
    except Exception:
        pass
    return "cpu", "int8"


def _is_downloaded(model: str) -> bool:
    try:
        from faster_whisper.utils import download_model
        download_model(model, local_files_only=True)
        return True
    except Exception:
        return False


def _get_model(model: str, device: str, compute: str, log):
    key = (model, device)
    if key in _models:
        if log:
            log(f"Using already loaded Whisper '{model}' on {device}.")
        return _models[key]
    if log:
        if _is_downloaded(model):
            log(f"Loading Whisper '{model}' on {device}...")
        else:
            log(f"Downloading Whisper '{model}' (first use only), then loading on {device}...")
    from faster_whisper import WhisperModel  # heavy import, load lazily
    _models[key] = WhisperModel(model, device=device, compute_type=compute)
    return _models[key]


def _decode_options(language: str | None) -> dict:
    return {
        "language": language,
        "beam_size": 5,
        "vad_filter": True,
        "vad_parameters": {"min_silence_duration_ms": 500},
        "condition_on_previous_text": False,  # stops one error from repeating through a long video
    }


def _run(wm, path: Path, cb, log, language: str | None = None) -> Transcript:
    segments_iter, info = wm.transcribe(str(path), **_decode_options(language))
    if log:
        log(f"Detected language: {info.language}")
    segments = []
    for s in segments_iter:
        segments.append(Segment(s.start, s.end, s.text.strip()))
        if cb and info.duration:
            cb(min(s.end / info.duration, 1.0))
    return Transcript(segments, info.language)


def transcribe(path: Path, model: str = "small",
               cb: Callable[[float], None] | None = None,
               log: Callable[[str], None] | None = None,
               language: str | None = None) -> Transcript:
    """Transcribe an audio file with faster-whisper, falling back to CPU if the GPU fails."""
    global _cuda_broken
    device, compute = _device()
    try:
        return _run(_get_model(model, device, compute, log), path, cb, log, language)
    except Exception as e:
        if device != "cuda":
            raise
        _cuda_broken = True
        _models.pop((model, "cuda"), None)
        if log:
            log(f"GPU failed ({type(e).__name__}: {e}). Using CPU instead.")
        return _run(_get_model(model, "cpu", "int8", log), path, cb, log, language)
