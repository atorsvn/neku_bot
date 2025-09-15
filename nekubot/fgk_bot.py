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
    clean_up,
)


class FGKBot(commands.Cog):
    """Core functionality for the Neku Discord bot."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = load_json("config/bot_config.json")
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
        clean_up()
        result = self.generator.run(user_id, da_text)
        audio_objects = [
            {"text": item["text"], "audio": item["audio_base64"]}
            for item in result["audio_data"]
        ]
        concatenate_texts(audio_objects)
        await do_tts(audio_objects)
        frame_sequence = await audio_analysis("crockpot/merged_sox.mp3")
        await create_grid_video(frame_sequence, self.grid)
        await add_vid_subs("crockpot/output_with_audio.mp4", "crockpot/neku.mp4")
        await ctx.reply(file=discord.File(r"crockpot/neku.mp4"))


def setup(bot: commands.Bot) -> None:
    """Compatibility helper for legacy extension loading."""
    bot.add_cog(FGKBot(bot))
