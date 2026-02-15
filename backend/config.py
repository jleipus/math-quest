from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DAIS_", env_file=".env", extra="ignore")

    app_name: str = "DAIS Active Learning API"
    app_version: str = "0.1.0"

    curriculum_source_url: str = "https://www.matteboken.se/lektioner/mellanstadiet/"
    curriculum_cache_ttl_seconds: int = 60 * 60

    assistant_confidence_threshold: float = Field(default=0.6, ge=0.0, le=1.0)

    llm_provider: str = "gemini"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"
    gemini_api_base: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_temperature: float = Field(default=0.2, ge=0.0, le=2.0)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
