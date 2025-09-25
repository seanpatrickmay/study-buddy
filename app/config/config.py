from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Optional, List
from pathlib import Path
import os

class Settings(BaseSettings):
    """Application configuration settings"""
    
    # API Keys
    openai_api_key: str = Field(..., env='OPENAI_API_KEY')
    tavily_api_key: str = Field(..., env='TAVILY_API_KEY')
    firecrawl_api_key: Optional[str] = Field(None, env='FIRECRAWL_API_KEY')
    anthropic_api_key: Optional[str] = Field(None, env='ANTHROPIC_API_KEY')
    
    # Model Configuration
    llm_model: str = Field('gpt-4-turbo-preview', env='LLM_MODEL')
    llm_temperature: float = Field(0.7, env='LLM_TEMPERATURE')
    max_tokens: int = Field(2000, env='MAX_TOKENS')
    
    # CrewAI Settings
    crew_verbose: bool = Field(True, env='CREW_VERBOSE')
    max_iter: int = Field(5, env='MAX_ITER')
    
    # File Paths
    upload_dir: Path = Field(Path("./uploads"), env='UPLOAD_DIR')
    output_dir: Path = Field(Path("./outputs"), env='OUTPUT_DIR')
    temp_dir: Path = Field(Path("./temp"), env='TEMP_DIR')
    
    # Processing Settings
    max_file_size_mb: int = Field(50, env='MAX_FILE_SIZE_MB')
    supported_formats: List[str] = [".pdf", ".txt", ".md"]
    
    # Anki Settings
    anki_deck_name: str = Field("AI Generated Study Deck", env='ANKI_DECK_NAME')
    anki_model_id: int = Field(1607392319, env='ANKI_MODEL_ID')
    anki_deck_id: int = Field(2059400110, env='ANKI_DECK_ID')
    
    # Rate Limiting
    tavily_rate_limit: int = Field(100, env='TAVILY_RATE_LIMIT')
    enable_caching: bool = Field(True, env='ENABLE_CACHING')
    cache_ttl: int = Field(3600, env='CACHE_TTL')
    
    @validator('upload_dir', 'output_dir', 'temp_dir')
    def create_directories(cls, v):
        """Ensure directories exist"""
        v = Path(v)
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    @validator('openai_api_key', 'tavily_api_key')
    def validate_required_keys(cls, v, field):
        """Validate required API keys"""
        if not v or v == "sk-..." or v == "tvly-...":
            raise ValueError(f"{field.name} must be set in .env file")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
    def get_model_config(self) -> dict:
        """Get model configuration for LangChain"""
        return {
            "model": self.llm_model,
            "temperature": self.llm_temperature,
            "max_tokens": self.max_tokens,
            "api_key": self.openai_api_key
        }

# Create settings instance
settings = Settings()