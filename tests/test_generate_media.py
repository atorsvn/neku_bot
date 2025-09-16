"""Tests for the offline media generation helper."""

import asyncio
import base64
import json
from pathlib import Path


async def fake_do_tts(segments, work_dir):
    mp3_path = Path(work_dir) / "merged.mp3"
    mp3_path.write_bytes(b"mp3")
    srt_path = Path(work_dir) / "subs.srt"
    srt_path.write_text("1\n00:00:00,000 --> 00:00:01,000\nHello\n\n", encoding="utf-8")
    return str(mp3_path), str(srt_path)


async def fake_audio_analysis(filepath):
    assert Path(filepath).exists()
    return [0, 1]


async def fake_create_grid_video(frame_sequence, grid, audio_path, work_dir):
    assert frame_sequence == [0, 1]
    video_path = Path(work_dir) / "grid.mp4"
    video_path.write_text("video", encoding="utf-8")
    return str(video_path)


async def fake_add_vid_subs(vid_in, srt_file, vid_out):
    assert Path(vid_in).exists()
    assert Path(srt_file).exists()
    Path(vid_out).write_text("final", encoding="utf-8")


class DummyGenerator:
    def __init__(self):
        self.calls = []

    def run(self, user_id, prompt):
        self.calls.append((user_id, prompt))
        return {
            "emotion": {"label": "happy", "score": 0.99},
            "audio_data": [
                {
                    "text": "Hello",
                    "audio_base64": base64.b64encode(b"chunk").decode("utf-8"),
                }
            ],
        }


def test_build_media_assets_writes_outputs(tmp_path):
    from nekubot.generate_media import build_media_assets

    generator = DummyGenerator()

    result = asyncio.run(
        build_media_assets(
            "hello",
            config_path="ignored.json",
            output_dir=str(tmp_path),
            generator=generator,
            grid=[[None]],
            do_tts_fn=fake_do_tts,
            audio_analysis_fn=fake_audio_analysis,
            create_grid_video_fn=fake_create_grid_video,
            add_vid_subs_fn=fake_add_vid_subs,
        )
    )

    assert generator.calls == [("offline-user", "hello")]

    video_path = Path(result["video"])
    audio_path = Path(result["audio"])
    srt_path = Path(result["srt"])
    segments_path = Path(result["segments"])

    assert video_path.exists()
    assert audio_path.exists()
    assert srt_path.exists()
    assert segments_path.exists()

    data = json.loads(segments_path.read_text(encoding="utf-8"))
    assert data["emotion"]["label"] == "happy"
    assert base64.b64decode(data["audio_data"][0]["audio_base64"]) == b"chunk"

    assert result["emotion"]["label"] == "happy"
