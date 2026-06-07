from functools import lru_cache

from backend.config import get_settings
from backend.services.llm.base import LLMProvider, LLMService


def _build_provider() -> LLMProvider:
    settings = get_settings()
    provider = settings.llm_provider.lower()

    if provider == "gemini":
        if not settings.gemini_api_key:
            raise ValueError("DAIS_GEMINI_API_KEY is required when llm_provider=gemini")
        from backend.services.llm.gemini import GeminiProvider

        return GeminiProvider()

    if provider == "claude":
        if not settings.claude_api_key:
            raise ValueError("DAIS_CLAUDE_API_KEY is required when llm_provider=claude")
        from backend.services.llm.claude import ClaudeProvider

        return ClaudeProvider()

    raise ValueError(f"Unknown llm_provider: {settings.llm_provider!r}. Choose mock, gemini, or claude.")


@lru_cache(maxsize=1)
def get_llm_service() -> LLMService:
    return LLMService(_build_provider())


def __getattr__(name: str) -> object:
    # Lazily build the service on first access so that merely importing this
    # package (e.g. to reach submodules in tests) doesn't require an API key.
    if name == "llm_service":
        return get_llm_service()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
