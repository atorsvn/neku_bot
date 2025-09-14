"""Tests for configuration helpers."""

import importlib.util
import json
from pathlib import Path


def load_config_module():
    path = Path(__file__).resolve().parent.parent / "nekubot" / "config.py"
    spec = importlib.util.spec_from_file_location("config", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_round_trip_json(tmp_path):
    """Saving and loading JSON should preserve the original data."""
    cfg = load_config_module()
    data = {"name": "Neku", "value": 42}
    file_path = tmp_path / "data.json"

    cfg.save_json(file_path, data)
    loaded = cfg.load_json(file_path)

    assert loaded == data
