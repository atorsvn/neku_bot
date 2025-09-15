"""Neku Bot package initialization."""

from .fgk_bot import FGKBot
from .discord_bot import NekuBot
from . import config, media, outworld, context, tts

__version__ = "0.1.0"

__all__ = [
    "FGKBot",
    "NekuBot",
    "config",
    "media",
    "outworld",
    "context",
    "tts",
]
