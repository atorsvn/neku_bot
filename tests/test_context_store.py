"""Tests for the ContextStore helper."""

import importlib.util
from pathlib import Path


def load_context_module():
    path = Path(__file__).resolve().parent.parent / "nekubot" / "context.py"
    spec = importlib.util.spec_from_file_location("context", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_context_store_trims_history():
    ctx = load_context_module()
    store = ctx.ContextStore(db_path=":memory:")
    for i in range(ctx.MAX_CONTEXT_HISTORY + 2):
        store.save_message("user", "role", f"msg{i}")
    context = store.get_context("user")
    assert len(context) == ctx.MAX_CONTEXT_HISTORY
    assert context[0]["content"] == "msg2"
