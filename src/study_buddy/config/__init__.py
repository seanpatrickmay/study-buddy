"""Configuration utilities for the Study Buddy application."""

from .config import (
    ANTHROPIC_MODEL_ALIASES,
    DEFAULT_ANTHROPIC_MODEL,
    Settings,
    settings,
)

__all__ = [
    "Settings",
    "settings",
    "DEFAULT_ANTHROPIC_MODEL",
    "ANTHROPIC_MODEL_ALIASES",
]
