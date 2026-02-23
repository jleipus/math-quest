"""Mock LLM provider — no network calls, deterministic enough for dev/testing."""

import random

from backend.services.llm.base import HelpResponse, LLMProvider


class MockProvider(LLMProvider):
    def __init__(self) -> None:
        self._rng = random.Random()

    def guide_student(
        self,
        question: str,
        context: str,
        image_png: bytes | None,
    ) -> HelpResponse:
        guiding_question = (
            f"What is the first step you would take to solve: {question} — "
            "can you think about what operation to use?"
        )
        return HelpResponse(
            guiding_question=guiding_question,
            context_used="(mock — no LLM configured)",
        )

    def _mock_confidence(self, question: str, image_png: bytes) -> float:
        complexity = min(len(question) / 120.0, 0.35)
        image_signal = min(len(image_png) / 25000.0, 0.45)
        noise = self._rng.uniform(0.05, 0.2)
        return round(min(complexity + image_signal + noise, 0.98), 2)
