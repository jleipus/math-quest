import json
import os
import re
from threading import Lock
from typing import Literal, cast
from uuid import uuid4

from huggingface_hub import InferenceClient

from backend.config import get_settings
from backend.models.assistant import AnalyseData
from backend.models.task import TaskItem
from backend.services.curriculum import curriculum_service


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
    def generate_tasks(self, topic: str, difficulty: str, count: int) -> list[TaskItem]:
        requested_topic = topic.strip()
        if not requested_topic:
            raise ValueError("Topic cannot be empty")
        normalized_topic = requested_topic.lower()

        settings = get_settings()
        if settings.llm_provider != "huggingface":
            raise RuntimeError(f"Unsupported LLM provider: {settings.llm_provider}")

        hf_token = settings.hf_token.strip() or os.environ.get("HF_TOKEN", "").strip()
        if not hf_token:
            raise RuntimeError("Missing HF token")

        try:
            provider = cast(Literal["featherless-ai"], settings.hf_provider)
            client = InferenceClient(provider=provider, api_key=hf_token)
        except RuntimeError as exc:
            raise RuntimeError("Hugging Face task generation failed") from exc

        collected_pairs: list[tuple[str, str]] = []
        duplicate_pairs: list[tuple[str, str]] = []
        seen_questions: set[str] = set()
        curriculum_hint = self._build_curriculum_hint(requested_topic)

        for _ in range(4):
            remaining = count - len(collected_pairs)
            if remaining <= 0:
                break

            avoid_block = self._build_avoid_block(collected_pairs)

            prompt = (
                "You create child-friendly math practice problems.\n"
                "Output exactly one JSON object with this shape:\n"
                "{\"tasks\":[{\"question\":\"What is 3 + 4?\",\"expected_answer\":\"7\"}]}\n"
                "Rules:\n"
                "- Use only the requested topic and difficulty.\n"
                "- Return exactly the requested count.\n"
                "- Ensure every expected_answer is mathematically correct.\n"
                "- Keep questions concise, natural, and suitable for children.\n"
                "- Write questions as full prompts (example: 'What is 3 + 4?').\n"
                "- Do not put the final result in the question text.\n"
                "- Avoid repeating the same question.\n"
                "- No markdown, no extra keys, no extra text.\n"
                f"topic: {requested_topic}\n"
                f"difficulty: {difficulty}\n"
                f"count: {remaining}\n"
                f"{curriculum_hint}\n"
                f"{avoid_block}"
            )

            try:
                response_text = client.text_generation(
                    prompt,
                    model=settings.hf_model,
                    temperature=0.4,
                    max_new_tokens=700,
                    return_full_text=False,
                )
            except RuntimeError as exc:
                raise RuntimeError("Hugging Face task generation failed") from exc

            raw_pairs = self._parse_generated_tasks(response_text, remaining, normalized_topic)
            for question, expected_answer in raw_pairs:
                dedupe_key = re.sub(r"\s+", " ", question.strip().lower())
                pair = (question, expected_answer)
                if dedupe_key in seen_questions:
                    duplicate_pairs.append(pair)
                    continue
                seen_questions.add(dedupe_key)
                collected_pairs.append(pair)
                if len(collected_pairs) >= count:
                    break

        single_attempts = 0
        while len(collected_pairs) < count and single_attempts < 14:
            single_attempts += 1
            avoid_block = self._build_avoid_block(collected_pairs)
            single_prompt = (
                "Create exactly one child-friendly math practice task.\n"
                f"Topic: {requested_topic}. Difficulty: {difficulty}.\n"
                "Do not repeat previous questions.\n"
                "Return exactly two lines and nothing else:\n"
                "Question: What is 3 + 4?\n"
                "Answer: 7\n"
                f"{curriculum_hint}\n"
                f"{avoid_block}"
            )

            try:
                single_text = client.text_generation(
                    single_prompt,
                    model=settings.hf_model,
                    temperature=0.4,
                    max_new_tokens=180,
                    return_full_text=False,
                )
            except RuntimeError as exc:
                raise RuntimeError("Hugging Face task generation failed") from exc

            single_pairs = self._parse_generated_tasks(single_text, 1, normalized_topic)
            if not single_pairs:
                continue
            question, expected_answer = single_pairs[0]
            dedupe_key = re.sub(r"\s+", " ", question.strip().lower())
            pair = (question, expected_answer)
            if dedupe_key in seen_questions:
                duplicate_pairs.append(pair)
                continue
            seen_questions.add(dedupe_key)
            collected_pairs.append(pair)

        while len(collected_pairs) < count and duplicate_pairs:
            collected_pairs.append(duplicate_pairs.pop(0))

        if len(collected_pairs) != count:
            raise RuntimeError("Generated task count mismatch")

        return [
            TaskItem(
                task_id=uuid4(),
                question=question,
                expected_answer=expected_answer,
                topic=normalized_topic,
                difficulty=difficulty,
            )
            for question, expected_answer in collected_pairs
        ]

    @staticmethod
    def _build_avoid_block(collected_pairs: list[tuple[str, str]]) -> str:
        if not collected_pairs:
            return "Avoid these questions: none"

        recent_questions = [question for question, _ in collected_pairs[-8:]]
        bullet_list = "\n".join(f"- {question}" for question in recent_questions)
        return f"Avoid these questions:\n{bullet_list}"

    @staticmethod
    def _build_curriculum_hint(requested_topic: str) -> str:
        try:
            topics = curriculum_service.get_topics()
        except RuntimeError:
            return "Curriculum context unavailable; proceed with the requested topic."

        if not topics:
            return "Curriculum context unavailable; proceed with the requested topic."

        names = [topic.name for topic in topics[:12]]
        topic_list = ", ".join(names)
        return (
            f"Curriculum topics from source: {topic_list}. "
            f"Prioritize alignment with '{requested_topic}' while keeping the problem age-appropriate."
        )

    def analyse_student_work(self, question: str, student_text: str, expected_answer: str | None = None) -> AnalyseData:
        settings = get_settings()

        normalized_text = student_text.strip() if student_text else ""
        if not normalized_text:
            return AnalyseData(
                has_issue=False,
                message="I couldn't clearly read the writing yet. Please write the numbers a bit bigger and darker.",
                suggestion="Write one step per line so I can check it accurately.",
                confidence=0.0,
            )

        normalized_text = self._normalize_ocr_math_text(
            question=question,
            student_text=normalized_text,
            expected_answer=expected_answer,
        )

        if settings.llm_provider != "huggingface":
            raise RuntimeError(f"Unsupported LLM provider: {settings.llm_provider}")

        llm_result = self._analyse_with_huggingface(question=question, student_text=normalized_text)
        if llm_result is None:
            raise RuntimeError("Hugging Face analysis failed")

        if llm_result.confidence < settings.assistant_confidence_threshold:
            return AnalyseData(
                has_issue=False,
                message="I need a little clearer writing to check this confidently.",
                suggestion="Write the full equation and answer on separate lines, then submit again.",
                confidence=llm_result.confidence,
            )

        return llm_result

    @staticmethod
    def _normalize_ocr_math_text(question: str, student_text: str, expected_answer: str | None) -> str:
        cleaned = student_text.strip()
        if not cleaned:
            return cleaned

        canonical = cleaned.replace("×", "*").replace("x", "*").replace("X", "*")
        canonical = re.sub(r"\s+", " ", canonical)

        match = re.search(r"(\d+)\s*([+\-*/])\s*(\d+)\s*([=_\-~]+)\s*(-?\d+)", canonical)
        if not match:
            return canonical

        left_val = int(match.group(1))
        operator = match.group(2)
        right_val = int(match.group(3))
        separator = match.group(4)
        result_val = int(match.group(5))

        computed = LLMService._compute_binary_result(left_val, operator, right_val)
        if computed is None:
            return canonical

        expected_val = LLMService._parse_expected_numeric(expected_answer)
        question_op = LLMService._extract_question_operator(question)

        looks_like_equals_misread = (
            "=" not in separator
            and any(ch in separator for ch in "-_~")
            and computed == result_val
            and (expected_val is None or expected_val == result_val)
            and (question_op is None or question_op == operator)
        )

        if looks_like_equals_misread:
            start, end = match.span(4)
            canonical = canonical[:start] + "=" + canonical[end:]

        return canonical

    @staticmethod
    def _compute_binary_result(left: int, operator: str, right: int) -> int | None:
        if operator == "+":
            return left + right
        if operator == "-":
            return left - right
        if operator == "*":
            return left * right
        if operator == "/":
            if right == 0:
                return None
            if left % right != 0:
                return None
            return left // right
        return None

    @staticmethod
    def _parse_expected_numeric(expected_answer: str | None) -> int | None:
        if not expected_answer:
            return None
        text = expected_answer.strip()
        if re.fullmatch(r"-?\d+", text):
            return int(text)
        return None

    @staticmethod
    def _extract_question_operator(question: str) -> str | None:
        normalized = question.replace("×", "*").replace("x", "*").replace("X", "*")
        for op in ("+", "-", "*", "/"):
            if op in normalized:
                return op
        return None

    def _analyse_with_huggingface(self, question: str, student_text: str) -> AnalyseData | None:
        settings = get_settings()
        hf_token = settings.hf_token.strip() or os.environ.get("HF_TOKEN", "").strip()
        if not hf_token:
            raise RuntimeError("Missing HF token")

        normalized_text = student_text.strip() if student_text else ""

        prompt = (
            "You are a kid-friendly math feedback assistant.\n"
            "Given a task and OCR text, decide if there is a likely math issue.\n"
            "Output exactly one JSON object with keys: has_issue, message, suggestion, confidence.\n"
            "Rules:\n"
            "- has_issue is true only when there is a clear math error.\n"
            "- If text is unclear/incomplete, set has_issue to false and ask for clearer writing.\n"
            "- confidence is a number between 0 and 1.\n"
            "- No markdown, no explanations, JSON only.\n"
            f"task_question: {question}\n"
            f"student_work_text: {normalized_text or '[no recognized text]'}"
        )

        try:
            provider = cast(Literal["featherless-ai"], settings.hf_provider)
            client = InferenceClient(provider=provider, api_key=hf_token)
            response_text = client.text_generation(
                prompt,
                model=settings.hf_model,
                temperature=settings.hf_temperature,
                max_new_tokens=240,
                return_full_text=False,
            )

            payload_text = self._extract_json_object(response_text)
            if payload_text:
                parsed = json.loads(payload_text)
                if isinstance(parsed, list):
                    if not parsed:
                        return None
                    parsed_obj = parsed[0]
                elif isinstance(parsed, dict):
                    parsed_obj = parsed
                else:
                    # Unexpected JSON shape
                    return None
                analysis = AnalyseData.model_validate(parsed_obj)
            else:
                analysis = self._coerce_analysis_from_text(response_text)

            normalized_confidence = max(0.0, min(1.0, analysis.confidence))
            return AnalyseData(
                has_issue=analysis.has_issue,
                message=analysis.message,
                suggestion=analysis.suggestion,
                confidence=round(normalized_confidence, 2),
            )
        except (ValueError, TypeError, json.JSONDecodeError, RuntimeError):
            return None

    @staticmethod
    def _coerce_analysis_from_text(response_text: str) -> AnalyseData:
        cleaned = response_text.strip()
        cleaned = re.sub(r"^```(?:json)?|```$", "", cleaned, flags=re.IGNORECASE | re.MULTILINE).strip()
        lowered = cleaned.lower()

        prompt_echo_markers = [
            "output exactly one json object",
            "no markdown, no explanations",
            "task_question:",
            "student_work_text:",
        ]

        if any(marker in lowered for marker in prompt_echo_markers):
            return AnalyseData(
                has_issue=False,
                message="I couldn't fully understand the written steps yet. Please write one step per line.",
                suggestion="Try writing the full equation and result clearly.",
                confidence=0.2,
            )

        issue_patterns = [
            r"\bincorrect\b",
            r"\bwrong\b",
            r"\berror\b",
            r"\bnot\s+correct\b",
            r"\bshould\s+be\b",
            r"\bdoesn['’]t\s+equal\b",
        ]
        ok_patterns = [
            r"\bcorrect\b",
            r"\bright\b",
            r"\bgood\s+job\b",
            r"\bwell\s+done\b",
            r"\blooks\s+good\b",
        ]

        issue_hits = any(re.search(pattern, lowered) for pattern in issue_patterns)
        ok_hits = any(re.search(pattern, lowered) for pattern in ok_patterns)

        if issue_hits and not ok_hits:
            has_issue = True
            confidence = 0.55
        elif ok_hits and not issue_hits:
            has_issue = False
            confidence = 0.45
        else:
            has_issue = False
            confidence = 0.2

        message = cleaned if cleaned else "Try checking your last step once more."
        if len(message) > 220:
            message = message[:220].rstrip() + "..."

        suggestion = (
            "Compare your last step with the operation in the question."
            if has_issue
            else "Write the full equation and answer clearly so I can verify it."
        )

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

    @staticmethod
    def _extract_json_array(text: str) -> str | None:
        stripped = text.strip()
        if stripped.startswith("```"):
            stripped = stripped.strip("`")
            if stripped.startswith("json"):
                stripped = stripped[4:].strip()

        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, list):
                return stripped
        except json.JSONDecodeError:
            pass

        start = stripped.find("[")
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
            elif ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    end = i
                    break

        if end == -1 or end <= start:
            return None

        candidate = stripped[start : end + 1]
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, list):
                return candidate
            return None
        except json.JSONDecodeError:
            return None

    def _parse_generated_tasks(self, response_text: str, count: int, topic: str) -> list[tuple[str, str]]:
        parsed_json: object | None = None

        stripped = response_text.strip()
        try:
            parsed_json = json.loads(stripped)
        except json.JSONDecodeError:
            array_payload = self._extract_json_array(response_text)
            if array_payload:
                try:
                    parsed_json = json.loads(array_payload)
                except json.JSONDecodeError:
                    parsed_json = None
            if parsed_json is None:
                object_payload = self._extract_json_object(response_text)
                if object_payload:
                    try:
                        parsed_json = json.loads(object_payload)
                    except json.JSONDecodeError:
                        parsed_json = None

        candidates: list[tuple[str, str]] = []
        if isinstance(parsed_json, dict):
            raw_tasks = parsed_json.get("tasks")
            if isinstance(raw_tasks, list):
                for item in raw_tasks:
                    if not isinstance(item, dict):
                        continue
                    question = str(item.get("question", "")).strip()
                    expected_answer = str(item.get("expected_answer", "")).strip()
                    normalized = self._normalize_generated_pair(question, expected_answer, topic)
                    if normalized is not None:
                        candidates.append(normalized)
        elif isinstance(parsed_json, list):
            for item in parsed_json:
                if not isinstance(item, dict):
                    continue
                question = str(item.get("question", "")).strip()
                expected_answer = str(item.get("expected_answer", "")).strip()
                normalized = self._normalize_generated_pair(question, expected_answer, topic)
                if normalized is not None:
                    candidates.append(normalized)

        if candidates:
            return candidates[:count]

        line_pairs = re.findall(
            r"(?:^|\n)\s*(?:\d+[\.)]\s*)?(?:Q(?:uestion)?\s*[:\-])\s*(.+?)\s*(?:\n|\s+)\s*(?:\d+[\.)]\s*)?(?:A(?:nswer)?\s*[:\-])\s*(.+?)(?=\n\s*(?:\d+[\.)]\s*)?(?:Q(?:uestion)?\s*[:\-])|\Z)",
            response_text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        normalized_pairs = [
            self._normalize_generated_pair(
                q.strip(),
                re.split(r"\n\s*(?:topic|difficulty)\s*:", a.strip(), flags=re.IGNORECASE)[0].strip(),
                topic,
            )
            for q, a in line_pairs
        ]
        normalized_pairs = [
            pair for pair in normalized_pairs if pair is not None
        ]
        return normalized_pairs[:count]

    def _normalize_generated_pair(self, question: str, expected_answer: str, topic: str) -> tuple[str, str] | None:
        if not self._is_valid_generated_field(question) or not self._is_valid_generated_field(expected_answer):
            return None

        cleaned_question = question.strip().strip('"').strip("'")
        cleaned_question = re.sub(r"^[-*\d\.)\s]+", "", cleaned_question).strip()
        cleaned_answer = expected_answer.strip().strip('"').strip("'")

        if "=" in cleaned_question and "?" not in cleaned_question:
            left, right = cleaned_question.split("=", 1)
            left_expr = left.strip().lstrip("+-×*/÷ ")
            right_expr = right.strip()
            if left_expr:
                cleaned_question = f"What is {left_expr}?"
            if right_expr and self._is_valid_generated_field(right_expr):
                cleaned_answer = right_expr

        if not cleaned_question.endswith("?"):
            cleaned_question = cleaned_question.rstrip(".") + "?"

        if not self._is_valid_generated_field(cleaned_question) or not self._is_valid_generated_field(cleaned_answer):
            return None

        if not self._is_plausible_question_for_topic(cleaned_question, topic):
            return None

        if len(cleaned_question) < 6 or len(cleaned_answer) < 1:
            return None

        answer_words = cleaned_answer.split()
        if len(answer_words) > 2:
            return None
        if re.search(r"\b(question|answer|topic|difficulty|string)\b", cleaned_answer, flags=re.IGNORECASE):
            return None

        return cleaned_question, cleaned_answer

    @staticmethod
    def _is_plausible_question_for_topic(question: str, topic: str) -> bool:
        lowered = question.lower()
        numbers = re.findall(r"\d+", lowered)

        if len(numbers) < 2:
            return False

        if topic == "addition":
            return "+" in lowered or "add" in lowered or "sum" in lowered
        if topic == "subtraction":
            return "-" in lowered or "subtract" in lowered or "minus" in lowered
        if topic == "multiplication":
            return "×" in lowered or "*" in lowered or " x " in lowered or "times" in lowered or "multiply" in lowered
        if topic == "fractions":
            return "/" in lowered

        return True

    @staticmethod
    def _is_valid_generated_field(value: str) -> bool:
        cleaned = value.strip()
        if not cleaned:
            return False

        lowered = cleaned.lower()
        disallowed_snippets = [
            "<question>",
            "<answer>",
            "question:",
            "answer:",
            "topic:",
            "difficulty:",
        ]
        if any(snippet in lowered for snippet in disallowed_snippets):
            return False

        disallowed_exact_values = {
            "string",
            "question",
            "answer",
            "<question>",
            "<answer>",
            "n/a",
            "na",
            "none",
            "null",
        }
        return lowered not in disallowed_exact_values

llm_service = LLMService()
task_registry = TaskRegistry()
