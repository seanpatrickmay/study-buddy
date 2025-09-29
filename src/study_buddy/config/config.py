"""Application-wide configuration powered by Pydantic settings."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralised configuration for Study Buddy services."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    openai_api_key: str = Field(...)
    tavily_api_key: Optional[str] = Field(None)
    firecrawl_api_key: Optional[str] = Field(None)

    vector_db_path: Path = Field(Path("./chroma_db"))
    embedding_model: str = Field("text-embedding-3-small")
    chunk_size: int = Field(1_000)
    chunk_overlap: int = Field(200)

    llm_model: str = Field("gpt-4o-mini")
    llm_temperature: float = Field(0.3)
    max_tokens: int = Field(2_000)

    upload_dir: Path = Field(Path("./uploads"))
    output_dir: Path = Field(Path("./outputs"))
    max_file_size_mb: int = Field(50)

    anki_deck_name: str = Field("Study Buddy Deck")
    anki_model_id: int = Field(1607392319)
    anki_deck_id: int = Field(2059400110)

    @field_validator("openai_api_key")
    def _require_openai(cls, value: str) -> str:
        if not value:
            raise ValueError("OPENAI_API_KEY is required for Study Buddy to operate.")
        return value

    @field_validator("upload_dir", "output_dir", "vector_db_path")
    def _ensure_directory(cls, value: Path) -> Path:
        path = Path(value)
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
