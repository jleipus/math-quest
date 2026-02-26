import random
from uuid import uuid4

from backend.models.game import Task
from backend.services.llm.base import HelpResponse, LLMProvider, _parse_hand_slots


class MockProvider(LLMProvider):
    def __init__(self) -> None:
        self._rng = random.Random()

    def generate_guidance(
        self,
        question: str,
        context: str,
        image_png: bytes | None,
        profile_context: str = "",
    ) -> HelpResponse:
        return HelpResponse(
            guiding_question=(
                f"What is the first step you would take to solve: {question} — "
                "can you think about what operation to use?"
            ),
            context_used="(mock — no LLM configured)",
        )

    def generate_task(
        self, grade: str, topic: str, difficulty: str, curriculum_context: str = "", profile_context: str = ""
    ) -> Task:
        lo, hi = {"easy": (1, 10), "medium": (10, 50)}.get(difficulty, (25, 120))
        a, b = self._rng.randint(lo, hi), self._rng.randint(lo, hi)

        t = topic.lower()
        if "subtraktion" in t:
            a, b = max(a, b), min(a, b)
            question, answer = f"What is {a} - {b}?", str(a - b)
        elif "multiplikation" in t:
            lo, hi = {"easy": (1, 10), "medium": (2, 12)}.get(difficulty, (3, 20))
            a, b = self._rng.randint(lo, hi), self._rng.randint(lo, hi)
            question, answer = f"What is {a} x {b}?", str(a * b)
        elif "division" in t:
            lo, hi = {"easy": (1, 10), "medium": (2, 12)}.get(difficulty, (3, 20))
            b = self._rng.randint(lo, hi)
            result = self._rng.randint(lo, hi)
            question, answer = f"What is {b * result} ÷ {b}?", str(result)
        elif "bråk" in t or "decimaltal" in t:
            denom = {"easy": 4, "medium": 8}.get(difficulty, 12)
            a, b = self._rng.randint(1, denom - 1), self._rng.randint(1, denom - 1)
            question, answer = f"What is {a}/{denom} + {b}/{denom}?", f"{a + b}/{denom}"
        else:
            question, answer = f"What is {a} + {b}?", str(a + b)

        return Task(
            task_id=uuid4(),
            question=question,
            expected_answer=answer,
            grade=grade,
            topic=topic,
            difficulty=difficulty,
        )

    def select_hand_slots(self, topics: list[str], profile_context: str, hand_size: int) -> list[tuple[str, str]]:
        difficulties = ["easy", "easy", "medium", "medium", "hard"]
        shuffled = list(topics)
        self._rng.shuffle(shuffled)
        slots = []
        for i in range(hand_size):
            topic = shuffled[i % len(shuffled)]
            difficulty = difficulties[i % len(difficulties)]
            slots.append((topic, difficulty))
        return slots
