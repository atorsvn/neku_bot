"""Tests for the :mod:`nekubot.outworld` module using lightweight stubs."""

import importlib.util
import json
import sys
import types
from pathlib import Path


def load_outworld_with_stubs():
    """Load the OutworldGenerator with external dependencies stubbed."""
    # Create stub modules for heavy dependencies before loading the module.
    fake_nltk = types.ModuleType("nltk")
    fake_nltk.download = lambda *a, **k: None
    fake_nltk.sent_tokenize = lambda text: [text]
    fake_nltk.data = types.SimpleNamespace(find=lambda *a, **k: None)
    sys.modules.setdefault("nltk", fake_nltk)

    fake_kokoro = types.ModuleType("kokoro")
    fake_kokoro.KPipeline = lambda lang_code: (
        lambda text, voice, speed, split_pattern=None: [("synthetic", "phonemes", b"00")]
    )
    sys.modules.setdefault("kokoro", fake_kokoro)

    class DummyChatResponse:
        def __init__(self, content: str):
            self.message = types.SimpleNamespace(content=content)

    fake_ollama = types.ModuleType("ollama")
    fake_ollama.ChatResponse = DummyChatResponse
    fake_ollama.chat = lambda model, messages: DummyChatResponse("hi")
    sys.modules.setdefault("ollama", fake_ollama)

    fake_transformers = types.ModuleType("transformers")
    fake_transformers.pipeline = (
        lambda *a, **k: (lambda text, truncation=True, max_length=512: [[{"label": "happy", "score": 1.0}]])
    )
    sys.modules.setdefault("transformers", fake_transformers)

    fake_sf = types.ModuleType("soundfile")
    fake_sf.write = lambda *a, **k: None
    sys.modules.setdefault("soundfile", fake_sf)

    # Register a lightweight package placeholder so relative imports succeed
    package = types.ModuleType("nekubot")
    package.__path__ = [str(Path(__file__).resolve().parent.parent / "nekubot")]
    sys.modules.setdefault("nekubot", package)

    module_path = Path(__file__).resolve().parent.parent / "nekubot" / "outworld.py"
    spec = importlib.util.spec_from_file_location("nekubot.outworld", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_run_creates_context_and_audio(tmp_path):
    outworld = load_outworld_with_stubs()

    config_file = tmp_path / "bot_config.json"
    config_file.write_text(json.dumps({"bot_name": "Test"}))

    generator = outworld.OutworldGenerator(config_path=str(config_file), db_path=":memory:")
    result = generator.run("user", "hello")

    assert result["emotion"]["label"] == "happy"
    assert result["audio_data"][0]["text"] == "synthetic"
    context = generator.get_context("user")
    assert len(context) == 2  # user message + assistant response
