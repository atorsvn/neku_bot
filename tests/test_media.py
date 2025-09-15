"""Tests for media helper functions."""

import importlib.util
from pathlib import Path

import asyncio
import numpy as np
import sys
import types


def load_media_module():
    sys.modules["cv2"] = types.ModuleType("cv2")
    path = Path(__file__).resolve().parent.parent / "nekubot" / "media.py"
    spec = importlib.util.spec_from_file_location("media", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_concatenate_texts():
    media = load_media_module()
    items = [{"text": "foo"}, {"text": "bar"}]
    assert media.concatenate_texts(items) == "foobar"


def test_audio_analysis_classifies_volume(tmp_path):
    media = load_media_module()
    sys.modules.pop("soundfile", None)
    import soundfile as sf
    sr = 16000
    data = np.concatenate([np.zeros(sr), np.ones(sr)])
    path = tmp_path / "test.wav"
    sf.write(path, data, sr)
    result = asyncio.run(media.audio_analysis(str(path)))
    assert len(result) > 0
    assert set(result).issubset({0, 1, 2})
