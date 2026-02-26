from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field


class Settings(BaseModel):

    app_name: str = "DAIS Active Learning API"
    app_version: str = "0.1.0"

    curriculum_source_url: str = "https://www.matteboken.se/lektioner/mellanstadiet/"
    curriculum_cache_ttl_seconds: int = 60 * 60

    assistant_confidence_threshold: float = Field(default=0.4, ge=0.0, le=1.0)

    llm_provider: Literal["huggingface"] = "huggingface"
    hf_provider: Literal["featherless-ai"] = "featherless-ai"
    hf_model: str = "AI-Sweden-Models/Llama-3-8B"
    hf_token: str = "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"
    hf_temperature: float = Field(default=0.2, ge=0.0, le=1.0)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.model_validate({})
