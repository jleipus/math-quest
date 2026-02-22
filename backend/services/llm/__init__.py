from backend.config import get_settings

from backend.models.assistant import HelpResponse, AnalysisResponse
from backend.services.llm.base import (
    LLMProvider,
    TaskGenerator,
    TaskRegistry,
)

from backend.models.game import Task


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


class LLMService(TaskGenerator):
    """
    Thin facade that combines deterministic task generation (TaskGenerator)
    with a swappable LLM provider for guide_student and analyse_student_work.
    """

    def __init__(self, provider: LLMProvider) -> None:
        super().__init__()
        self._provider = provider

    def guide_student(
        self,
        question: str,
        context: str,
        image_png: bytes | None = None,
    ) -> HelpResponse:
        return self._provider.guide_student(question, context, image_png)

    def analyse_student_work(self, question: str, image_png: bytes) -> AnalysisResponse:
        settings = get_settings()
        result = self._provider.analyse_student_work(question, image_png)
        if result.confidence < settings.assistant_confidence_threshold:
            return AnalysisResponse(
                has_issue=False,
                message="",
                suggestion="",
                confidence=result.confidence,
            )
        return result


task_registry = TaskRegistry()
llm_service = LLMService(_build_provider())
