"""Command-line helper to build media assets without Discord."""

from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Awaitable, Callable, Mapping, MutableMapping, Sequence

AudioSegment = Mapping[str, str]
GridType = Any
DoTTSFn = Callable[[Sequence[AudioSegment], str], Awaitable[tuple[str, str]]]
AudioAnalysisFn = Callable[[str], Awaitable[Sequence[int]]]
CreateGridVideoFn = Callable[[Sequence[int], GridType, str, str], Awaitable[str]]
AddVidSubsFn = Callable[[str, str, str], Awaitable[None]]


async def build_media_assets(
    prompt: str,
    *,
    config_path: str = "config/bot_config.json",
    output_dir: str | Path = "artifacts",
    user_id: str = "offline-user",
    model: str = "llama3.2",
    lang_code: str = "a",
    voice: str = "af_heart",
    speed: int = 1,
    db_path: str = "db/context_history.db",
    grid_rows: int = 3,
    grid_folder: str = "vids",
    generator: Any | None = None,
    grid: GridType | None = None,
    load_grid_fn: Callable[[int, str], GridType] | None = None,
    audio_analysis_fn: AudioAnalysisFn | None = None,
    create_grid_video_fn: CreateGridVideoFn | None = None,
    do_tts_fn: DoTTSFn | None = None,
    add_vid_subs_fn: AddVidSubsFn | None = None,
) -> MutableMapping[str, Any]:
    """Generate media files for ``prompt`` and save them to ``output_dir``.

    The helper mirrors the Discord pipeline but is usable offline. The
    dependencies can be injected, simplifying tests.
    """

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if generator is None:
        from .outworld import OutworldGenerator

        generator = OutworldGenerator(
            model=model,
            lang_code=lang_code,
            voice=voice,
            speed=speed,
            config_path=config_path,
            db_path=db_path,
        )

    media_module = None

    def _resolve_media_module():
        nonlocal media_module
        if media_module is None:
            from . import media as media_module_real

            media_module = media_module_real
        return media_module

    if grid is None:
        if load_grid_fn is None:
            load_grid_fn = _resolve_media_module().load_grid
        grid = load_grid_fn(grid_rows, grid_folder)

    if audio_analysis_fn is None:
        audio_analysis_fn = _resolve_media_module().audio_analysis
    if create_grid_video_fn is None:
        create_grid_video_fn = _resolve_media_module().create_grid_video
    if do_tts_fn is None:
        do_tts_fn = _resolve_media_module().do_tts
    if add_vid_subs_fn is None:
        add_vid_subs_fn = _resolve_media_module().add_vid_subs

    result = generator.run(user_id, prompt)
    audio_segments = result.get("audio_data", [])
    if not audio_segments:
        raise ValueError("Generator returned no audio data to synthesize")

    mp3_output = output_path / "response.mp3"
    srt_output = output_path / "response.srt"
    video_output = output_path / "response.mp4"
    segments_output = output_path / "response_segments.json"

    serializable_segments = [
        {"text": seg["text"], "audio": seg["audio_base64"]}
        for seg in audio_segments
    ]

    with tempfile.TemporaryDirectory() as work_dir:
        mp3_path, srt_path = await do_tts_fn(serializable_segments, work_dir)
        frame_sequence = await audio_analysis_fn(mp3_path)
        video_path = await create_grid_video_fn(
            frame_sequence, grid, mp3_path, work_dir
        )
        await add_vid_subs_fn(video_path, srt_path, str(video_output))

        shutil.copyfile(mp3_path, mp3_output)
        shutil.copyfile(srt_path, srt_output)

    with segments_output.open("w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)

    return {
        "video": str(video_output),
        "audio": str(mp3_output),
        "srt": str(srt_output),
        "segments": str(segments_output),
        "emotion": result.get("emotion", {}),
    }


def create_media_assets(prompt: str, **kwargs: Any) -> MutableMapping[str, Any]:
    """Synchronously run :func:`build_media_assets` using ``asyncio.run``."""

    return asyncio.run(build_media_assets(prompt, **kwargs))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate media artifacts using the Neku pipeline",
    )
    parser.add_argument("prompt", help="Prompt to feed into the generator")
    parser.add_argument(
        "--config-path",
        default="config/bot_config.json",
        help="Path to the bot configuration file",
    )
    parser.add_argument(
        "--output-dir",
        default="artifacts",
        help="Directory to store generated files",
    )
    parser.add_argument(
        "--user-id",
        default="offline-user",
        help="Identifier used when storing context",
    )
    parser.add_argument("--model", default="llama3.2", help="Ollama model name")
    parser.add_argument(
        "--lang-code",
        default="a",
        help="Kokoro language code ('a' for American English)",
    )
    parser.add_argument(
        "--voice", default="af_heart", help="Kokoro voice preset to use"
    )
    parser.add_argument(
        "--speed",
        default=1,
        type=int,
        help="Speech synthesis speed multiplier",
    )
    parser.add_argument(
        "--db-path",
        default="db/context_history.db",
        help="Location for the SQLite conversation store",
    )
    parser.add_argument(
        "--grid-folder",
        default="vids",
        help="Folder containing the grid animation MP4 files",
    )
    parser.add_argument(
        "--grid-rows",
        default=3,
        type=int,
        help="Number of rows in the animation grid",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the ``nekubot-generate-media`` console script."""

    parser = _build_parser()
    args = parser.parse_args(argv)
    result = create_media_assets(
        args.prompt,
        config_path=args.config_path,
        output_dir=args.output_dir,
        user_id=args.user_id,
        model=args.model,
        lang_code=args.lang_code,
        voice=args.voice,
        speed=args.speed,
        db_path=args.db_path,
        grid_folder=args.grid_folder,
        grid_rows=args.grid_rows,
    )

    emotion = result.get("emotion", {})
    score = emotion.get("score")
    if isinstance(score, (float, int)):
        score_text = f"{score:.2%}"
    else:
        score_text = str(score) if score is not None else "unknown"

    print(
        f"Emotion: {emotion.get('label', 'unknown')} (confidence: {score_text})",
    )
    print(f"Video saved to: {result['video']}")
    print(f"Audio saved to: {result['audio']}")
    print(f"Subtitles saved to: {result['srt']}")
    print(f"Segments JSON saved to: {result['segments']}")
    return 0


if __name__ == "__main__":  # pragma: no cover - manual invocation helper
    raise SystemExit(main())

