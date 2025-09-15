import os
import tempfile

import discord
from discord.ext import commands

from .config import load_json
from .outworld import OutworldGenerator
from .media import (
    load_grid,
    audio_analysis,
    create_grid_video,
    concatenate_texts,
    do_tts,
    add_vid_subs,
)


class FGKBot(commands.Cog):
    """Core functionality for the Neku Discord bot."""

    def __init__(self, bot: commands.Bot, config_path: str):
        self.bot = bot
        self.config = load_json(config_path)
        self.generator = OutworldGenerator(
            config=self.config, db_path="db/context_history.db"
        )
        self.grid = load_grid()

    async def avatar_waifu(
        self,
        ctx: commands.Context,
        da_text: str,
        user_name: str,
        user_id: int,
        channel_id: int,
    ) -> None:
        """Run the avatar_waifu pipeline and reply with the generated video."""
        result = self.generator.run(user_id, da_text)
        audio_objects = [
            {"text": item["text"], "audio": item["audio_base64"]}
            for item in result["audio_data"]
        ]
        concatenate_texts(audio_objects)
        with tempfile.TemporaryDirectory() as work_dir:
            mp3_path, srt_path = await do_tts(audio_objects, work_dir)
            frame_sequence = await audio_analysis(mp3_path)
            video_path = await create_grid_video(frame_sequence, self.grid, mp3_path, work_dir)
            final_video = os.path.join(work_dir, "spongebob.mp4")
            await add_vid_subs(video_path, srt_path, final_video)
            await ctx.reply(file=discord.File(final_video))


def setup(bot: commands.Bot) -> None:
    """Compatibility helper for legacy extension loading."""
    bot.add_cog(FGKBot(bot, "config/bot_config.json"))
