from abc import ABC, abstractmethod
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

TASK_SYSTEM_PROMPT = (
    "You are a math task generator for Swedish primary school students (Mellanstadiet, ages 10-12). "
    "Generate a single math task appropriate for the given grade and topic. "
    "Rules: "
    "- The task must be solvable with a single numeric or fractional answer. "
    "- Write the question in English. "
    "- Respond with exactly two lines: the first line is the question, the second is the answer. "
    "- No explanation, no preamble, no extra lines."
)


def build_guide_user_text(question: str, context: str, has_image: bool, profile_context: str = "") -> str:
    text = f"Curriculum context:\n{context}\n\nMath task the student is working on:\n{question}\n\n"
    if has_image:
        text += "The student has submitted handwritten work (see image). Please consider it.\n\n"
    if profile_context:
        text += f"{profile_context}\n\n"
    return text


def build_task_user_text(
    grade: str,
    topic: str,
    difficulty: str,
    curriculum_context: str = "",
    profile_context: str = "",
) -> str:
    text = f"Grade: {grade}\nTopic: {topic}\nDifficulty: {difficulty}"
    if curriculum_context:
        text += f"\n\nCurriculum context:\n{curriculum_context}"
    if profile_context:
        text += f"\n\n{profile_context}"
    return text


class LLMProvider(ABC):
    """Abstract interface for an LLM backend.

    Implementations must provide:
    - ``guide_student`` — returns a guiding question.
    - ``generate_task`` — generates a single math task for a grade/topic/difficulty.
    """

    @abstractmethod
    def generate_guidance(
        self,
        question: str,
        context: str,
        image_png: bytes | None,
        profile_context: str = "",
    ) -> HelpResponse: ...

    @abstractmethod
    def generate_task(
        self,
        grade: str,
        topic: str,
        difficulty: str,
        curriculum_context: str = "",
        profile_context: str = "",
    ) -> Task: ...


def _parse_task(text: str, grade: str, topic: str, difficulty: str) -> Task:
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    if len(lines) < 2:
        raise RuntimeError(f"Could not parse task from LLM response: {text!r}")
    return Task(
        task_id=uuid4(),
        question=lines[0],
        expected_answer=lines[1],
        grade=grade,
        topic=topic,
        difficulty=difficulty,
    )
