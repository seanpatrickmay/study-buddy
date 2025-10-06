"""Application-wide configuration powered by Pydantic settings."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


DEFAULT_ANTHROPIC_MODEL = "claude-3-haiku-20240307"
ANTHROPIC_MODEL_ALIASES: dict[str, str] = {
    "claude-3-5-sonnet-20241022": DEFAULT_ANTHROPIC_MODEL,
    "anthropic/claude-3-5-sonnet-20241022": DEFAULT_ANTHROPIC_MODEL,
    "claude-3-5-sonnet-20240620": DEFAULT_ANTHROPIC_MODEL,
    "anthropic/claude-3-5-sonnet-20240620": DEFAULT_ANTHROPIC_MODEL,
    "claude-3-5-sonnet-latest": DEFAULT_ANTHROPIC_MODEL,
    "anthropic/claude-3-5-sonnet-latest": DEFAULT_ANTHROPIC_MODEL,
    "claude-3-sonnet-20240229": DEFAULT_ANTHROPIC_MODEL,
    "anthropic/claude-3-sonnet-20240229": DEFAULT_ANTHROPIC_MODEL,
    "claude-3-sonnet-latest": DEFAULT_ANTHROPIC_MODEL,
    "claude-3-opus-20240229": DEFAULT_ANTHROPIC_MODEL,
    "claude-3-opus-latest": DEFAULT_ANTHROPIC_MODEL,
}

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralised configuration for Study Buddy services."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    anthropic_api_key: str = Field(...)
    voyage_api_key: Optional[str] = Field(None)
    tavily_api_key: Optional[str] = Field(None)
    firecrawl_api_key: Optional[str] = Field(None)

    vector_db_path: Path = Field(Path("./chroma_db"))
    embedding_model: str = Field("voyage-3")
    chunk_size: int = Field(1_000)
    chunk_overlap: int = Field(200)

    llm_model: str = Field(DEFAULT_ANTHROPIC_MODEL)
    llm_temperature: float = Field(0.3)
    max_tokens: int = Field(2_000)

    upload_dir: Path = Field(Path("./uploads"))
    output_dir: Path = Field(Path("./outputs"))
    max_file_size_mb: int = Field(50)

    anki_deck_name: str = Field("Study Buddy Deck")
    anki_model_id: int = Field(1607392319)
    anki_deck_id: int = Field(2059400110)

    @field_validator("anthropic_api_key")
    def _require_anthropic(cls, value: str) -> str:
        if not value:
            raise ValueError("ANTHROPIC_API_KEY is required for Study Buddy to operate.")
        return value

    @field_validator("voyage_api_key")
    def _validate_voyage(cls, value: Optional[str]) -> Optional[str]:
        if value and not value.strip():
            return None
        return value

    @field_validator("llm_model")
    def _canonicalise_llm_model(cls, value: str) -> str:
        candidate = (value or "").strip()
        if not candidate:
            return DEFAULT_ANTHROPIC_MODEL
        lowered = candidate.lower()
        if lowered in ANTHROPIC_MODEL_ALIASES:
            return ANTHROPIC_MODEL_ALIASES[lowered]
        if candidate in ANTHROPIC_MODEL_ALIASES:
            return ANTHROPIC_MODEL_ALIASES[candidate]
        return candidate

    @field_validator("upload_dir", "output_dir", "vector_db_path")
    def _ensure_directory(cls, value: Path) -> Path:
        path = Path(value)
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()

if settings.anthropic_api_key:
    os.environ.setdefault("ANTHROPIC_API_KEY", settings.anthropic_api_key)
if settings.voyage_api_key:
    os.environ.setdefault("VOYAGE_API_KEY", settings.voyage_api_key)
if settings.tavily_api_key:
    os.environ.setdefault("TAVILY_API_KEY", settings.tavily_api_key)
if settings.firecrawl_api_key:
    os.environ.setdefault("FIRECRAWL_API_KEY", settings.firecrawl_api_key)
