import base64
import random
from threading import Lock
from uuid import uuid4

from backend.config import get_settings
from backend.models.assistant import AnalyseData
from backend.models.task import TaskItem


class TaskRegistry:
    def __init__(self) -> None:
        self._lock = Lock()
        self._tasks: dict[str, TaskItem] = {}

    def put_many(self, tasks: list[TaskItem]) -> None:
        with self._lock:
            for task in tasks:
                self._tasks[str(task.task_id)] = task

    def get(self, task_id: str) -> TaskItem | None:
        with self._lock:
            return self._tasks.get(task_id)


class LLMService:
    def __init__(self) -> None:
        self._rng = random.Random()

    def generate_tasks(self, topic: str, difficulty: str, count: int) -> list[TaskItem]:
        normalized_topic = topic.strip().lower()

        generators = {
            "addition": self._addition_question,
            "subtraction": self._subtraction_question,
            "multiplication": self._multiplication_question,
            "fractions": self._fractions_question,
        }
        generator = generators.get(normalized_topic, self._generic_question)

        tasks: list[TaskItem] = []
        for _ in range(count):
            question, answer = generator(difficulty, normalized_topic)
            tasks.append(
                TaskItem(
                    task_id=uuid4(),
                    question=question,
                    expected_answer=answer,
                    topic=normalized_topic,
                    difficulty=difficulty,
                )
            )
        return tasks

    def analyse_student_work(self, question: str, image_png: bytes) -> AnalyseData:

        settings = get_settings()

        if settings.llm_provider != "mock" and settings.llm_api_key:
            return AnalyseData(
                has_issue=False,
                message="",
                suggestion="",
                confidence=0.0,
            )

        confidence = self._mock_confidence(question, image_png)
        has_issue = confidence >= settings.assistant_confidence_threshold

        if not has_issue:
            return AnalyseData(
                has_issue=False,
                message="",
                suggestion="",
                confidence=confidence,
            )

        return AnalyseData(
            has_issue=True,
            message="Looks like there might be a mismatch with the required operation for this step.",
            suggestion="Check the operation sign in the question and try that step again.",
            confidence=confidence,
        )

    def _mock_confidence(self, question: str, image_png: bytes) -> float:
        complexity = min(len(question) / 120.0, 0.35)
        image_signal = min(len(image_png) / 25000.0, 0.45)
        noise = self._rng.uniform(0.05, 0.2)
        score = min(complexity + image_signal + noise, 0.98)
        return round(score, 2)

    def _difficulty_range(self, difficulty: str) -> tuple[int, int]:
        if difficulty == "easy":
            return (1, 10)
        if difficulty == "medium":
            return (10, 50)
        return (25, 120)

    def _addition_question(self, difficulty: str, _topic: str) -> tuple[str, str]:
        low, high = self._difficulty_range(difficulty)
        a = self._rng.randint(low, high)
        b = self._rng.randint(low, high)
        return (f"What is {a} + {b}?", str(a + b))

    def _subtraction_question(self, difficulty: str, _topic: str) -> tuple[str, str]:
        low, high = self._difficulty_range(difficulty)
        a = self._rng.randint(low, high)
        b = self._rng.randint(low, high)
        top, bottom = max(a, b), min(a, b)
        return (f"What is {top} - {bottom}?", str(top - bottom))

    def _multiplication_question(self, difficulty: str, _topic: str) -> tuple[str, str]:
        if difficulty == "easy":
            a = self._rng.randint(1, 10)
            b = self._rng.randint(1, 10)
        elif difficulty == "medium":
            a = self._rng.randint(6, 20)
            b = self._rng.randint(6, 20)
        else:
            a = self._rng.randint(12, 40)
            b = self._rng.randint(12, 40)
        return (f"What is {a} × {b}?", str(a * b))

    def _fractions_question(self, difficulty: str, _topic: str) -> tuple[str, str]:
        denominator = 4 if difficulty == "easy" else 8 if difficulty == "medium" else 12
        a = self._rng.randint(1, denominator - 1)
        b = self._rng.randint(1, denominator - 1)
        numerator = a + b
        return (
            f"What is {a}/{denominator} + {b}/{denominator}?",
            f"{numerator}/{denominator}",
        )

    def _generic_question(self, difficulty: str, topic: str) -> tuple[str, str]:
        low, high = self._difficulty_range(difficulty)
        a = self._rng.randint(low, high)
        b = self._rng.randint(low, high)
        return (
            f"Solve this {topic} task: {a} + {b}",
            str(a + b),
        )


llm_service = LLMService()
task_registry = TaskRegistry()
