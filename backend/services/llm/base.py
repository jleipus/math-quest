import random
from abc import ABC, abstractmethod
from threading import Lock
from uuid import uuid4

from backend.models.game import Task
from backend.models.assistant import HelpResponse


MINIGUIDE_SYSTEM_PROMPT = (
    "You are MiniGuide, a friendly math tutor for students aged 10-12."
    "Your ONLY job is to ask ONE short guiding question that nudges the student toward the answer."
    "Rules you must NEVER break:"
    "- Do NOT reveal the answer, or any part of it."
    '- Do NOT say "the answer is…", "you should get…", or anything that gives it away.'
    "- Do NOT perform the calculation for the student."
    "- Ask exactly one question — concise, age-appropriate, and encouraging."
    "- If the student has shared work, acknowledge what they have done so far before asking your question."
    "Respond with only the guiding question. No preamble, no explanation."
)


def build_guide_user_text(question: str, context: str, has_image: bool) -> str:
    text = f"Curriculum context:\n{context}\n\nMath task the student is working on:\n{question}\n\n"
    if has_image:
        text += "The student has submitted handwritten work (see image). Please consider it."
    return text


class TaskRegistry:
    def __init__(self) -> None:
        self._lock = Lock()
        self._tasks: dict[str, Task] = {}

    def put_many(self, tasks: list[Task]) -> None:
        with self._lock:
            for task in tasks:
                self._tasks[str(task.task_id)] = task

    def get(self, task_id: str) -> Task | None:
        with self._lock:
            return self._tasks.get(task_id)


class LLMProvider(ABC):
    """
    Abstract interface for an LLM backend.

    Implementations must provide:
    - guide_student   — MiniGuide: returns a guiding question, never the answer.
    - analyse_student_work — analyses handwritten work from a rasterised PNG.

    Task generation is for now deterministic, and lives in the concrete
    LLMService wrapper so it is shared across all providers.
    Actual tasks should be generated using curriculum data and LLM.
    """

    @abstractmethod
    def guide_student(
        self,
        question: str,
        context: str,
        image_png: bytes | None,
    ) -> HelpResponse: ...


class TaskGenerator:
    def __init__(self) -> None:
        self._rng = random.Random()

        self.__generators = {  # dict to easily pick generator by the topic
            "addition": self._addition,
            "subtraction": self._subtraction,
            "multiplication": self._multiplication,
            "fractions": self._fractions,
        }

    def generate_tasks(
        self,
        topic: str,
        difficulty: str,
        count: int,
    ) -> list[Task]:
        generator = self.__generators.get(topic, self._generic)
        return [
            Task(
                task_id=uuid4(),
                question=q,
                expected_answer=a,
                topic=topic,
                difficulty=difficulty,
            )
            for q, a in (generator(difficulty, topic) for _ in range(count))
        ]

    def _difficulty_range(self, difficulty: str) -> tuple[int, int]:
        return {"easy": (1, 10), "medium": (10, 50)}.get(difficulty, (25, 120))

    def _addition(self, difficulty: str, _: str) -> tuple[str, str]:
        lo, hi = self._difficulty_range(difficulty)
        a, b = self._rng.randint(lo, hi), self._rng.randint(lo, hi)
        return f"What is {a} + {b}?", str(a + b)

    def _subtraction(self, difficulty: str, _: str) -> tuple[str, str]:
        lo, hi = self._difficulty_range(difficulty)
        a, b = self._rng.randint(lo, hi), self._rng.randint(lo, hi)
        top, bot = max(a, b), min(a, b)
        return f"What is {top} - {bot}?", str(top - bot)

    def _multiplication(self, difficulty: str, _: str) -> tuple[str, str]:
        ranges = {"easy": (1, 10), "medium": (6, 20)}
        lo, hi = ranges.get(difficulty, (12, 40))
        a, b = self._rng.randint(lo, hi), self._rng.randint(lo, hi)
        return f"What is {a} x {b}?", str(a * b)

    def _fractions(self, difficulty: str, _: str) -> tuple[str, str]:
        denom = {"easy": 4, "medium": 8}.get(difficulty, 12)
        a, b = self._rng.randint(1, denom - 1), self._rng.randint(1, denom - 1)
        return f"What is {a}/{denom} + {b}/{denom}?", f"{a + b}/{denom}"

    def _generic(self, difficulty: str, topic: str) -> tuple[str, str]:
        lo, hi = self._difficulty_range(difficulty)
        a, b = self._rng.randint(lo, hi), self._rng.randint(lo, hi)
        return f"Solve this {topic} task: {a} + {b}", str(a + b)
