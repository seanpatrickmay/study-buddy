# config.py
from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    # API Keys
    openai_api_key: str
    tavily_api_key: str
    firecrawl_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # Model Configuration
    llm_model: str = "gpt-4-turbo-preview"
    llm_temperature: float = 0.7
    max_tokens: int = 2000
    
    # CrewAI Settings
    crew_verbose: bool = True
    max_iter: int = 5
    
    # File Paths
    upload_dir: Path = Path("./uploads")
    output_dir: Path = Path("./outputs")
    temp_dir: Path = Path("./temp")
    
    # Processing Settings
    max_file_size_mb: int = 50
    supported_formats: list = [".pdf", ".txt", ".md"]
    
    # Anki Settings
    anki_deck_name: str = "AI Generated Study Deck"
    anki_model_id: int = 1607392319
    anki_deck_id: int = 2059400110
    
    # Rate Limiting
    tavily_rate_limit: int = 100  # requests per minute
    enable_caching: bool = True
    cache_ttl: int = 3600  # seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()

# Create directories
settings.upload_dir.mkdir(exist_ok=True)
settings.output_dir.mkdir(exist_ok=True)
settings.temp_dir.mkdir(exist_ok=True)