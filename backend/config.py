from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DAIS_", env_file=".env", extra="ignore")

    app_name: str = "MathQuest API"
    app_version: str = "0.1.0"

    llm_provider: str = "mock"

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"
    gemini_api_base: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_temperature: float = Field(default=0.2, ge=0.0, le=1.0)

    claude_api_key: str | None = None
    claude_model: str = "claude-sonnet-4-5"

    player_start_hp: int = 100
    enemy_start_hp: int = 100
    default_hand_size: int = 5
    max_energy: int = 3

    chroma_db_path: str = "./data/chroma"
    tiiny_db_path: str = "./data/curriculum_tree.json"
    rag_top_k: int = 3


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
