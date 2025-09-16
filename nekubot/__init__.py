"""Neku Bot package initialization."""

from .fgk_bot import FGKBot
from .discord_bot import NekuBot
from .generate_media import create_media_assets, build_media_assets
from . import config, media, outworld, context, tts

__version__ = "0.1.0"

__all__ = [
    "FGKBot",
    "NekuBot",
    "create_media_assets",
    "build_media_assets",
    "config",
    "media",
    "outworld",
    "context",
    "tts",
]
