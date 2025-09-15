"""Neku Bot package initialization."""

from .fgk_bot import FGKBot
from . import config, media, outworld, context, tts

__all__ = ["FGKBot", "config", "media", "outworld", "context", "tts"]