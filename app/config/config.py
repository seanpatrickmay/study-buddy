from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
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

    # Firecrawl Settings
    firecrawl_max_urls: int = Field(5, env='FIRECRAWL_MAX_URLS')

    # Vector Database Settings
    vector_db_path: Path = Field(Path("./chroma_db"), env='VECTOR_DB_PATH')
    embedding_model: str = Field('text-embedding-ada-002', env='EMBEDDING_MODEL')

    # RAG Settings
    chunk_size: int = Field(1000, env='CHUNK_SIZE')
    chunk_overlap: int = Field(200, env='CHUNK_OVERLAP')
    
    # Tavily Settings (for LangChain-Tavily)
    tavily_search_depth: str = Field("basic", env='TAVILY_SEARCH_DEPTH')  # basic or advanced
    tavily_max_results: int = Field(3, env='TAVILY_MAX_RESULTS')
    tavily_include_answer: bool = Field(True, env='TAVILY_INCLUDE_ANSWER')
    tavily_include_raw_content: bool = Field(False, env='TAVILY_INCLUDE_RAW_CONTENT')
    tavily_rate_limit: int = Field(100, env='TAVILY_RATE_LIMIT')
    
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
    
    @field_validator('upload_dir', 'output_dir', 'temp_dir')
    def create_directories(cls, v: Path):
        """Ensure directories exist"""
        v = Path(v)
        v.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator('openai_api_key', 'tavily_api_key')
    def validate_required_keys(cls, v: str, info):
        """Validate required API keys"""
        if not v or v in ["sk-...", "tvly-..."]:
            raise ValueError(f"{info.field_name} must be set in .env file")
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