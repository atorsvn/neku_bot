import asyncio
import logging

import discord
from discord.ext import commands

from nekubot import FGKBot


def setup_logging():
    """Configure basic logging for the bot."""
    logging.basicConfig(
        level=logging.ERROR,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


async def run_avatar_waifu(ctx, query: str, fgk_bot: FGKBot) -> None:
    """Execute the avatar_waifu command and log any errors."""
    try:
        await fgk_bot.avatar_waifu(
            ctx,
            query,
            ctx.message.author.name,
            ctx.message.author.id,
            ctx.message.channel.id,
        )
    except Exception as exc:  # pragma: no cover - defensive logging
        logging.error("Error in neku command: %s", exc)


def create_bot() -> commands.Bot:
    """Create the Discord bot with the required intents."""
    intents = discord.Intents.default()
    intents.message_content = True
    return commands.Bot(command_prefix="!", intents=intents)


def configure_bot(bot: commands.Bot, fgk_bot: FGKBot) -> None:
    """Attach events and commands to the bot instance."""

    @bot.event
    async def on_ready() -> None:  # pragma: no cover - simple logging
        try:
            print(f"We have logged in as {bot.user}")
        except Exception as exc:
            logging.error("Error in on_ready: %s", exc)

    @bot.command(name="neku")
    async def neku(ctx: commands.Context, *, query: str = "") -> None:
        try:
            if ctx.message.author == bot.user:
                return
            async with ctx.typing():
                asyncio.create_task(run_avatar_waifu(ctx, query, fgk_bot))
        except Exception as exc:  # pragma: no cover - defensive logging
            logging.error("Error in neku command: %s", exc)


async def main() -> None:
    """Entry point for running the bot."""
    setup_logging()
    bot = create_bot()
    fgk_bot = FGKBot(bot)
    configure_bot(bot, fgk_bot)

    await bot.start(fgk_bot.config["DISCORD-TOKEN"])


if __name__ == "__main__":  # pragma: no cover - script entry point
    asyncio.run(main())