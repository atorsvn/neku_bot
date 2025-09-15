"""Discord bot wrapper that wires FGKBot into a runnable client."""

from __future__ import annotations

import asyncio
import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from .fgk_bot import FGKBot


class NekuBot:
    """Encapsulated Discord bot that loads configuration and runs FGKBot."""

    def __init__(self, config_path: str) -> None:
        load_dotenv()
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            raise RuntimeError("DISCORD_TOKEN not set in environment")
        self.token = token

        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix="!", intents=intents)
        self.cog = FGKBot(self.bot, config_path)
        self.bot.add_cog(self.cog)
        self._configure_events()

    def _configure_events(self) -> None:
        @self.bot.event
        async def on_ready() -> None:  # pragma: no cover - simple logging
            print(f"We have logged in as {self.bot.user}")

        @self.bot.command(name="neku")
        async def neku(ctx: commands.Context, *, query: str = "") -> None:
            if ctx.message.author == self.bot.user:
                return
            async with ctx.typing():
                asyncio.create_task(
                    self.cog.avatar_waifu(
                        ctx,
                        query,
                        ctx.message.author.name,
                        ctx.message.author.id,
                        ctx.message.channel.id,
                    )
                )

    def run(self) -> None:
        """Configure logging and start the Discord bot."""
        logging.basicConfig(
            level=logging.ERROR,
            format="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self.bot.run(self.token)

