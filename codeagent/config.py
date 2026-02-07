from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache

class Settings(BaseSettings):
    """
    Application Configuration loaded from environment variables and .env file.
    """
    # LLM Configuration
    openai_api_key: str = Field(..., description="API Key for OpenAI compatible provider")
    openai_base_url: str = Field(..., description="Base URL for OpenAI compatible provider")
    openai_model: str = Field("qwen-plus", description="Model name to use")
    
    # System Configuration
    log_level: str = Field("INFO", description="Logging level")
    debug_mode: bool = Field(False, description="Enable verbose trace logging to file")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

@lru_cache()
def get_settings() -> Settings:
    """
    Singleton pattern for Settings.
    Cached to prevent re-reading .env file on every call.
    """
    return Settings()
