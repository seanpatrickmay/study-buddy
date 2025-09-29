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

    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    tavily_api_key: Optional[str] = Field(None, env="TAVILY_API_KEY")
    firecrawl_api_key: Optional[str] = Field(None, env="FIRECRAWL_API_KEY")

    vector_db_path: Path = Field(Path("./chroma_db"), env="VECTOR_DB_PATH")
    embedding_model: str = Field("text-embedding-3-small", env="EMBEDDING_MODEL")
    chunk_size: int = Field(1_000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(200, env="CHUNK_OVERLAP")

    llm_model: str = Field("gpt-4o-mini", env="LLM_MODEL")
    llm_temperature: float = Field(0.3, env="LLM_TEMPERATURE")
    max_tokens: int = Field(2_000, env="MAX_TOKENS")

    upload_dir: Path = Field(Path("./uploads"), env="UPLOAD_DIR")
    output_dir: Path = Field(Path("./outputs"), env="OUTPUT_DIR")
    max_file_size_mb: int = Field(50, env="MAX_FILE_SIZE_MB")

    anki_deck_name: str = Field("Study Buddy Deck", env="ANKI_DECK_NAME")
    anki_model_id: int = Field(1607392319, env="ANKI_MODEL_ID")
    anki_deck_id: int = Field(2059400110, env="ANKI_DECK_ID")

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
