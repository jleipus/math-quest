from backend.config import get_settings
from backend.models.assistant import HelpResponse
from backend.models.game import Task
from backend.services.llm.base import LLMProvider


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

    if provider == "mock":
        from backend.services.llm.mock import MockProvider

        return MockProvider()

    raise ValueError(f"Unknown llm_provider: {settings.llm_provider!r}. Choose mock, gemini, or claude.")


class LLMService:
    """Wrapper for the LLMProvider."""

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    def generate_guidance(
        self,
        question: str,
        context: str,
        image_png: bytes | None = None,
        profile_context: str = "",
    ) -> HelpResponse:
        return self._provider.generate_guidance(question, context, image_png, profile_context)

    def generate_tasks(
        self,
        grade: str,
        topic: str,
        difficulty: str,
        count: int,
        curriculum_context: str = "",
        profile_context: str = "",
    ) -> list[Task]:
        return [self._provider.generate_task(grade, topic, difficulty, curriculum_context, profile_context) for _ in range(count)]


llm_service = LLMService(_build_provider())
