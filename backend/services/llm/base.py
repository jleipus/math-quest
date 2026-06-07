import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import uuid4

from backend.models.game import Task
from backend.models.assistant import HintResponse
from backend.services.logger import log
from backend.services.llm.prompts import (
    GUIDANCE_SYSTEM_PROMPT,
    TASK_SYSTEM_PROMPT,
    HAND_SELECTOR_SYSTEM_PROMPT,
    build_guide_user_text,
    build_hand_selector_text,
    build_task_text,
)


@dataclass
class LLMResult:
    """An LLM completion plus debug metrics about the call."""

    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: float | None = None


def _extract_json(text: str) -> dict:
    """Extract and parse the first complete JSON object from *text*."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise RuntimeError(f"No JSON object found in LLM response: {text!r}")
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in LLM response: {exc}\nRaw: {text!r}") from exc


def _parse_guidance(raw: str) -> str:
    """Extract ``guiding_question`` from a guidance JSON response."""
    data = _extract_json(raw)
    guiding_question = data.get("guiding_question", "")
    if not isinstance(guiding_question, str) or not guiding_question.strip():
        raise RuntimeError(f"Missing or empty 'guiding_question' in response: {raw!r}")
    return guiding_question.strip()


def _parse_tasks(raw: str, grade: str, topic: str) -> list[Task]:
    """Extract a list of tasks from a batch task JSON response."""
    valid_difficulties = {"easy", "medium", "hard"}
    valid_answer_types = {"number", "fraction", "text"}
    data = _extract_json(raw)
    raw_tasks = data.get("tasks", [])
    if not isinstance(raw_tasks, list):
        raise RuntimeError(f"'tasks' is not a list in LLM response: {raw!r}")

    tasks: list[Task] = []
    for item in raw_tasks:
        if not isinstance(item, dict):
            continue
        question = item.get("question", "")
        answer = item.get("answer", "")
        difficulty = str(item.get("difficulty", "")).lower()
        if (
            isinstance(question, str)
            and question.strip()
            and isinstance(answer, str)
            and answer.strip()
            and difficulty in valid_difficulties
        ):
            answer_type = str(item.get("answer_type", "number")).lower()
            if answer_type not in valid_answer_types:
                answer_type = "number"
            raw_accepted = item.get("accepted_answers", [])
            accepted_answers = (
                [a.strip() for a in raw_accepted if isinstance(a, str) and a.strip()]
                if isinstance(raw_accepted, list)
                else []
            )
            tasks.append(
                Task(
                    task_id=str(uuid4()),
                    question=question.strip(),
                    expected_answer=answer.strip(),
                    grade=grade,
                    topic=topic,
                    difficulty=difficulty,
                    answer_type=answer_type,  # type: ignore[arg-type]
                    accepted_answers=accepted_answers,
                )
            )

    if not tasks:
        raise RuntimeError(f"No valid tasks parsed from LLM response: {raw!r}")
    return tasks


def _parse_hand_slots(raw: str, valid_topics: set[str], hand_size: int) -> list[tuple[str, str]]:
    """Extract (topic, difficulty) pairs from a hand-selector JSON response."""
    valid_difficulties = {"easy", "medium", "hard"}
    data = _extract_json(raw)
    raw_slots = data.get("slots", [])
    if not isinstance(raw_slots, list):
        raise RuntimeError(f"'slots' is not a list in response: {raw!r}")

    slots: list[tuple[str, str]] = []
    for item in raw_slots:
        if not isinstance(item, dict):
            continue
        topic = item.get("topic", "")
        difficulty = str(item.get("difficulty", "")).lower()
        if topic in valid_topics and difficulty in valid_difficulties:
            slots.append((topic, difficulty))
        if len(slots) == hand_size:
            break
    return slots


class LLMProvider(ABC):
    """Abstract interface for an LLM backend."""

    @abstractmethod
    def call(
        self,
        prompt: str,
        system_prompt: str,
        image_png: bytes | None = None,
    ) -> LLMResult: ...


class LLMService:
    """Wrapper for the LLMProvider."""

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    @staticmethod
    def _log_metrics(ctx: dict, result: LLMResult) -> None:
        """Record token usage and response time for a completed LLM call."""
        ms = round(result.latency_ms, 1) if result.latency_ms is not None else None
        log(
            "llm_response",
            {
                **ctx,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "response_time_ms": ms,
            },
        )

    def generate_guidance(
        self,
        question: str,
        context: str,
        image_png: bytes | None = None,
        profile_context: str = "",
        previous_hints: list[str] | None = None,
        previous_attempts: list[str] | None = None,
        session_id: str | None = None,
    ) -> HintResponse:
        """Return guiding question generated by the LLM."""
        prompt = build_guide_user_text(
            question,
            context,
            has_image=bool(image_png),
            profile_context=profile_context,
            previous_hints=previous_hints,
            previous_attempts=previous_attempts,
        )
        ctx = {"session_id": session_id, "call": "generate_guidance"}

        log("llm_request", {**ctx, "question": question, "has_image": image_png is not None})
        try:
            result = self._provider.call(prompt, GUIDANCE_SYSTEM_PROMPT, image_png)
            self._log_metrics(ctx, result)
            guiding_question = _parse_guidance(result.text)
        except Exception as exc:
            log("llm_error", {**ctx, "error": str(exc)})
            raise

        return HintResponse(guiding_question=guiding_question)

    def generate_tasks_for_topic(
        self,
        grade: str,
        topic: str,
        difficulties: list[str],
        curriculum_context: str = "",
        profile_context: str = "",
        session_id: str | None = None,
    ) -> list[Task]:
        """Generate one task per requested difficulty for a single topic in one LLM call."""
        prompt = build_task_text(grade, topic, difficulties, curriculum_context, profile_context)
        ctx = {"session_id": session_id, "call": "generate_tasks_for_topic"}

        log("llm_request", {**ctx, "topic": topic, "difficulties": difficulties})
        try:
            result = self._provider.call(prompt, TASK_SYSTEM_PROMPT)
            self._log_metrics(ctx, result)
            tasks = _parse_tasks(result.text, grade, topic)
        except Exception as exc:
            log("llm_error", {**ctx, "error": str(exc)})
            raise

        return tasks

    def select_hand_slots(
        self,
        topics: list[str],
        profile_context: str,
        hand_size: int,
        session_id: str | None = None,
    ) -> list[tuple[str, str]]:
        """Return (topic, difficulty) pairs for the next hand, chosen by the LLM."""
        prompt = build_hand_selector_text(topics, profile_context, hand_size)
        ctx = {"session_id": session_id, "call": "select_hand_slots"}

        log("llm_request", {**ctx, "hand_size": hand_size})
        try:
            result = self._provider.call(prompt, HAND_SELECTOR_SYSTEM_PROMPT)
            self._log_metrics(ctx, result)
            slots = _parse_hand_slots(result.text, set(topics), hand_size)
        except Exception as exc:
            log("llm_error", {**ctx, "error": str(exc)})
            raise

        return slots
