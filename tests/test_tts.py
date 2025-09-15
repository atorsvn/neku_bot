"""Tests for the KokoroTTS helper with stubbed dependencies."""

import base64
import importlib.util
import sys
import types
from pathlib import Path


def load_tts_with_stubs():
    sys.modules.pop("nltk", None)
    fake_nltk = types.ModuleType("nltk")
    fake_nltk.sent_tokenize = lambda text: [text]
    fake_nltk.data = types.SimpleNamespace(find=lambda *a, **k: None)
    sys.modules["nltk"] = fake_nltk

    sys.modules.pop("kokoro", None)
    fake_kokoro = types.ModuleType("kokoro")
    fake_kokoro.KPipeline = lambda lang_code: (
        lambda text, voice, speed, split_pattern=None: [(text, "ph", b"audio")]
    )
    sys.modules["kokoro"] = fake_kokoro

    sys.modules.pop("soundfile", None)
    fake_sf = types.ModuleType("soundfile")
    fake_sf.write = lambda buffer, audio, sr, format="WAV": buffer.write(audio)
    sys.modules["soundfile"] = fake_sf

    module_path = Path(__file__).resolve().parent.parent / "nekubot" / "tts.py"
    spec = importlib.util.spec_from_file_location("tts", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_text_to_audio_returns_base64():
    tts = load_tts_with_stubs().KokoroTTS()
    result = tts.text_to_audio("hello")
    assert result[0]["text"] == "hello"
    assert base64.b64decode(result[0]["audio_base64"]) == b"audio"
