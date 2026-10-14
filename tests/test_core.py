from app import exporter, settings
from app.downloader import audio_bitrate, safe_name, video_format
from app.transcriber import Segment, Transcript


def sample():
    return Transcript([Segment(0, 2, "Hello"), Segment(3725, 3730, "Zdravo, čšž")], "en")


def test_fmt_time():
    assert exporter.fmt_time(65) == "01:05"
    assert exporter.fmt_time(3725) == "1:02:05"


def test_markdown(tmp_path):
    p = exporter.write_markdown(sample(), "T", "http://x", tmp_path / "a.md")
    text = p.read_text(encoding="utf-8")
    assert "# T" in text and "**[1:02:05]** Zdravo, čšž" in text


def test_pdf(tmp_path):
    p = exporter.write_pdf(sample(), "Naslov čšž", "http://x", tmp_path / "a.pdf")
    assert p.read_bytes().startswith(b"%PDF")


def test_safe_name():
    assert safe_name('a/b:c?"d" ') == "a_b_c__d_"
    assert safe_name("") == "untitled"


def test_settings_roundtrip(tmp_path):
    f = tmp_path / "c.json"
    d = settings.load(f)
    d["model"] = "tiny"
    settings.save(d, f)
    assert settings.load(f)["model"] == "tiny"


def test_quality_mapping():
    assert audio_bitrate("128 kbps") == "128"
    assert audio_bitrate("junk") == "320"
    assert "height<=720" in video_format("720p")
    assert video_format("Best") == "bestvideo*+bestaudio/best"
    assert video_format("junk") == "bestvideo*+bestaudio/best"


def test_gpu_failure_logs_reason_and_falls_back(monkeypatch):
    from app import transcriber as t

    class Fake:
        def __init__(self, dev): self.dev = dev
        def transcribe(self, path, **opts):
            if self.dev == "cuda":
                raise RuntimeError("cublas64_12.dll missing")
            return iter([]), type("I", (), {"language": "en", "duration": 1})()

    monkeypatch.setattr(t, "_models", {})
    monkeypatch.setattr(t, "_cuda_broken", False)
    monkeypatch.setattr(t, "_device", lambda: ("cuda", "float16"))
    monkeypatch.setattr(t, "_get_model", lambda m, d, c, log: Fake(d))
    logs = []
    t.transcribe("x.wav", "tiny", None, logs.append)
    assert any("cublas64_12.dll missing" in m for m in logs)
    assert t._cuda_broken is True
    monkeypatch.setattr(t, "_cuda_broken", False)


def test_model_cache_and_messages(monkeypatch):
    from app import transcriber as t
    import faster_whisper

    created = []
    monkeypatch.setattr(faster_whisper, "WhisperModel", lambda *a, **k: created.append(a) or object())
    monkeypatch.setattr(t, "_models", {})
    monkeypatch.setattr(t, "_is_downloaded", lambda m: False)
    logs = []
    t._get_model("tiny", "cpu", "int8", logs.append)
    assert "Downloading" in logs[0]
    monkeypatch.setattr(t, "_is_downloaded", lambda m: True)
    t._get_model("tiny", "cpu", "int8", logs.append)
    assert "already loaded" in logs[1] and len(created) == 1
    t._models.clear()
    t._get_model("tiny", "cpu", "int8", logs.append)
    assert logs[2].startswith("Loading") and "Downloading" not in logs[2]


def test_settings_per_screen_dirs_default_from_output_dir(tmp_path):
    p = tmp_path / "config.json"
    p.write_text('{"output_dir": "X"}', encoding="utf-8")
    cfg = settings.load(p)
    assert cfg["audio_dir"].endswith("audio") and cfg["video_dir"].endswith("video")
    assert cfg["transcribe_dir"].endswith("transcripts")
    p.write_text('{"audio_dir": "A"}', encoding="utf-8")
    assert settings.load(p)["audio_dir"] == "A"


def test_decode_options():
    from app.transcriber import _decode_options
    o = _decode_options(None)
    assert o["language"] is None and o["beam_size"] == 5 and o["vad_filter"] is True
    assert o["condition_on_previous_text"] is False
    assert _decode_options("en")["language"] == "en"


def test_audio_prep_falls_back_when_ffmpeg_fails(monkeypatch, tmp_path):
    import subprocess
    from app import audio_prep

    def boom(*a, **k):
        raise FileNotFoundError("ffmpeg")
    monkeypatch.setattr(subprocess, "run", boom)
    src = tmp_path / "a.m4a"
    logs = []
    assert audio_prep.prepare(src, tmp_path, logs.append) == src
    assert logs


def test_settings_default_language():
    assert settings.DEFAULTS["language"] == "Auto"


def test_is_playlist_url():
    from app.downloader import is_playlist_url
    assert is_playlist_url("https://www.youtube.com/playlist?list=PL123")
    assert is_playlist_url("https://youtube.com/watch?list=PL123")
    assert not is_playlist_url("https://www.youtube.com/watch?v=abc&list=PL123")
    assert not is_playlist_url("https://youtu.be/abc")
    assert not is_playlist_url("garbage")


def test_parse_playlist_skips_unavailable_and_builds_urls():
    from app.downloader import parse_playlist
    title, entries = parse_playlist({"title": "Moja lista čšž", "entries": [
        {"id": "a1", "title": "Prva"},
        {"id": "b2", "title": "[Private video]"},
        None,
        {"id": "c3", "title": "Treća"},
    ]})
    assert title == "Moja lista čšž"
    assert [(e.index, e.id) for e in entries] == [(1, "a1"), (4, "c3")]
    assert entries[0].url == "https://www.youtube.com/watch?v=a1"


def test_item_prefix_and_outtmpl(tmp_path):
    from app.downloader import _outtmpl, item_prefix
    assert item_prefix(3, 9) == "03 - "
    assert item_prefix(7, 120) == "007 - "
    assert _outtmpl(tmp_path, "01 - ").endswith("01 - %(title).120B.%(ext)s")
    assert _outtmpl(tmp_path).endswith("%(title).120B.%(ext)s")
