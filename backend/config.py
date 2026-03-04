from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DAIS_", env_file=".env", extra="ignore")

    # App
    app_name: str = "MathQuest API"
    app_version: str = "0.1.0"

    # Security
    allowed_origins: list[str] = ["http://localhost:3000"]
    api_key: str | None = None  # If set, all /api/v1 requests must supply X-API-Key header

    # LLMs
    llm_provider: str = "claude"

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"
    gemini_api_base: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_temperature: float = Field(default=0.2, ge=0.0, le=1.0)

    claude_api_key: str | None = None
    claude_model: str = "claude-sonnet-4-5"
    claude_api_base: str = "https://api.anthropic.com/v1"

    # Game mechanics
    player_start_hp: int = 100
    enemy_start_hp: int = 100
    default_hand_size: int = 5
    max_energy: int = 3

    # RAG & user modelling
    rag_top_k: int = 3
    chroma_db_path: str = "./data/chroma"
    tiny_db_path: str = "./data/curriculum_tree.json"
    user_model_db_path: str = "./data/user_models.json"

    # Logging
    llm_log_path: str | None = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
