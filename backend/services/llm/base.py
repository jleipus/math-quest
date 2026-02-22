import json
import random
from abc import ABC, abstractmethod
from threading import Lock
from uuid import uuid4

from backend.models.game import Task
from backend.models.assistant import HelpResponse, AnalysisResponse


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

ANALYSE_SYSTEM_PROMPT = (
    "You are a kid-friendly math handwriting assistant. "
    "Analyze the student's in-progress math work image for likely mistakes. "
    "Return ONLY valid JSON with keys: has_issue (boolean), message (string), "
    "suggestion (string), confidence (number between 0 and 1). "
    "Use concise, child-friendly language."
)


def build_guide_user_text(question: str, context: str, has_image: bool) -> str:
    text = f"Curriculum context:\n{context}\n\nMath task the student is working on:\n{question}\n\n"
    if has_image:
        text += "The student has submitted handwritten work (see image). Please consider it."
    return text


def build_analyse_user_text(question: str) -> str:
    return f"Task question: {question}"


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


def extract_json_object(text: str) -> str | None:
    """Extract the first JSON object from a string, stripping markdown fences."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.startswith("json"):
            stripped = stripped[4:].strip()

    try:
        json.loads(stripped)
        return stripped
    except json.JSONDecodeError:
        pass

    start = stripped.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False
    end = -1
    for i, ch in enumerate(stripped[start:], start=start):
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i
                break

    if end == -1 or end <= start:
        return None
    candidate = stripped[start : end + 1]
    try:
        json.loads(candidate)
        return candidate
    except json.JSONDecodeError:
        return None


def coerce_analysis_from_text(response_text: str) -> AnalysisResponse:
    """Best-effort parse of an AnalyseResponse from plain text when JSON is unavailable."""
    lowered = response_text.lower()
    issue_markers = ["wrong", "incorrect", "mistake", "error", "check", "not correct"]
    has_issue = any(marker in lowered for marker in issue_markers)

    message = response_text.strip() or "Try checking your last step once more."
    if len(message) > 220:
        message = message[:220].rstrip() + "..."

    suggestion = (
        "Compare your last step with the operation in the question."
        if has_issue
        else "Good progress — continue to the next step."
    )
    confidence = 0.55 if has_issue else 0.45
    return AnalysisResponse(
        has_issue=has_issue,
        message=message,
        suggestion=suggestion,
        confidence=confidence,
    )


def parse_analyse_response(response_text: str) -> AnalysisResponse | None:
    """Parse and normalise an AnalyseResponse from a model's text output."""
    payload_text = extract_json_object(response_text)
    if payload_text:
        try:
            parsed = json.loads(payload_text)
            if isinstance(parsed, list):
                if not parsed:
                    return None
                parsed = parsed[0]
            if not isinstance(parsed, dict):
                return None
            analysis = AnalysisResponse.model_validate(parsed)
        except (json.JSONDecodeError, ValueError):
            analysis = coerce_analysis_from_text(response_text)
    else:
        analysis = coerce_analysis_from_text(response_text)

    confidence = round(max(0.0, min(1.0, analysis.confidence)), 2)
    return AnalysisResponse(
        has_issue=analysis.has_issue,
        message=analysis.message,
        suggestion=analysis.suggestion,
        confidence=confidence,
    )


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

    @abstractmethod
    def analyse_student_work(
        self,
        question: str,
        image_png: bytes,
    ) -> AnalysisResponse: ...


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
