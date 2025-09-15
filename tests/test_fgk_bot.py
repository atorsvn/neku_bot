"""Tests for the FGKBot pipeline with stubbed media and generator."""

import asyncio
import base64
import importlib.util
import os
import sys
import types
from pathlib import Path

import discord
from discord.ext import commands


def load_fgk_bot_with_stubs():
    sys.modules.pop("nekubot.outworld", None)
    stub_outworld = types.ModuleType("nekubot.outworld")

    class DummyGenerator:
        def __init__(self, *a, **k):
            pass

        def run(self, user_id, da_text):
            return {
                "audio_data": [
                    {
                        "text": "hi",
                        "audio_base64": base64.b64encode(b"00").decode(),
                    }
                ]
            }

    stub_outworld.OutworldGenerator = DummyGenerator
    sys.modules["nekubot.outworld"] = stub_outworld

    sys.modules.pop("nekubot.media", None)
    stub_media = types.ModuleType("nekubot.media")
    stub_media.load_grid = lambda: [[None]]

    async def fake_audio_analysis(path):
        return [0]

    async def fake_create_grid_video(frame_sequence, grid, mp3_path, work_dir):
        video_path = os.path.join(work_dir, "grid.mp4")
        open(video_path, "wb").write(b"vid")
        return video_path

    async def fake_do_tts(audio_objects, work_dir):
        mp3_path = os.path.join(work_dir, "merged.mp3")
        open(mp3_path, "wb").write(b"mp3")
        srt_path = os.path.join(work_dir, "subs.srt")
        open(srt_path, "w").write("1\n00:00:00,000 --> 00:00:01,000\nhi\n")
        return mp3_path, srt_path

    async def fake_add_vid_subs(video_path, srt_path, final_video):
        open(final_video, "wb").write(b"final")

    stub_media.audio_analysis = fake_audio_analysis
    stub_media.create_grid_video = fake_create_grid_video
    stub_media.do_tts = fake_do_tts
    stub_media.add_vid_subs = fake_add_vid_subs
    stub_media.concatenate_texts = lambda objs: "".join(o["text"] for o in objs)
    sys.modules["nekubot.media"] = stub_media

    sys.modules.pop("nekubot.config", None)
    stub_config = types.ModuleType("nekubot.config")
    stub_config.load_json = lambda path: {}
    sys.modules["nekubot.config"] = stub_config

    package = types.ModuleType("nekubot")
    package.__path__ = [str(Path(__file__).resolve().parent.parent / "nekubot")]
    sys.modules.setdefault("nekubot", package)

    module_path = Path(__file__).resolve().parent.parent / "nekubot" / "fgk_bot.py"
    spec = importlib.util.spec_from_file_location("nekubot.fgk_bot", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class DummyCtx:
    def __init__(self):
        self.file = None

    async def reply(self, file):
        self.file = file


def test_avatar_waifu_creates_video():
    fgk_mod = load_fgk_bot_with_stubs()
    bot = commands.Bot(command_prefix="!", intents=discord.Intents.none())
    fgk = fgk_mod.FGKBot(bot, "config/bot_config.json")
    ctx = DummyCtx()
    asyncio.run(fgk.avatar_waifu(ctx, "hello", "user", 1, 1))
    assert ctx.file.filename == "spongebob.mp4"
