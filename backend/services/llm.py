import base64
import json
import random
from threading import Lock
from uuid import uuid4

import requests

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

        if settings.llm_provider == "gemini":
            llm_result = self._analyse_with_gemini(question=question, image_png=image_png)
            if llm_result is not None:
                if llm_result.confidence < settings.assistant_confidence_threshold:
                    return AnalyseData(
                        has_issue=False,
                        message="",
                        suggestion="",
                        confidence=llm_result.confidence,
                    )
                return llm_result

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

    def _analyse_with_gemini(self, question: str, image_png: bytes) -> AnalyseData | None:
        settings = get_settings()
        if not settings.gemini_api_key:
            return None

        image_b64 = base64.b64encode(image_png).decode("utf-8")

        prompt = (
            "You are a kid-friendly math handwriting assistant. "
            "Analyze the student's in-progress math work image for likely mistakes. "
            "Return ONLY valid JSON with keys: has_issue (boolean), message (string), "
            "suggestion (string), confidence (number between 0 and 1). "
            "Use concise, child-friendly language. "
            f"Task question: {question}"
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": image_b64,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "temperature": settings.gemini_temperature,
                "responseMimeType": "application/json",
            },
        }

        url = (
            f"{settings.gemini_api_base}/models/{settings.gemini_model}:generateContent"
            f"?key={settings.gemini_api_key}"
        )

        try:
            response = requests.post(url, json=payload, timeout=25)
            response.raise_for_status()
            result = response.json()

            response_text = self._extract_gemini_text(result)
            if not response_text:
                return None

            payload_text = self._extract_json_object(response_text)
            if payload_text:
                parsed = json.loads(payload_text)
                if isinstance(parsed, list) and parsed:
                    parsed = parsed[0]
                analysis = AnalyseData.model_validate(parsed)
            else:
                analysis = self._coerce_analysis_from_text(response_text)

            normalized_confidence = max(0.0, min(1.0, analysis.confidence))
            return AnalyseData(
                has_issue=analysis.has_issue,
                message=analysis.message,
                suggestion=analysis.suggestion,
                confidence=round(normalized_confidence, 2),
            )
        except (requests.RequestException, ValueError, TypeError, json.JSONDecodeError):
            return None

    @staticmethod
    def _extract_gemini_text(result: dict) -> str | None:
        candidates = result.get("candidates", [])
        for candidate in candidates:
            content = candidate.get("content", {})
            for part in content.get("parts", []):
                text = part.get("text")
                if isinstance(text, str) and text.strip():
                    return text

        prompt_feedback = result.get("promptFeedback", {})
        block_reason = prompt_feedback.get("blockReason")
        if block_reason:
            return f"Request blocked: {block_reason}"
        return None

    @staticmethod
    def _coerce_analysis_from_text(response_text: str) -> AnalyseData:
        lowered = response_text.lower()
        issue_markers = ["wrong", "incorrect", "mistake", "error", "check", "not correct"]
        has_issue = any(marker in lowered for marker in issue_markers)

        message = response_text.strip()
        if not message:
            message = "Try checking your last step once more."

        if len(message) > 220:
            message = message[:220].rstrip() + "..."

        suggestion = (
            "Compare your last step with the operation in the question."
            if has_issue
            else "Good progress — continue to the next step."
        )

        confidence = 0.72 if has_issue else 0.58
        return AnalyseData(
            has_issue=has_issue,
            message=message,
            suggestion=suggestion,
            confidence=confidence,
        )

    @staticmethod
    def _extract_json_object(text: str) -> str | None:
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
        end = stripped.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None

        candidate = stripped[start : end + 1]
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            return None

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
