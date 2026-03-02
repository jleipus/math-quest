from abc import ABC, abstractmethod
from uuid import uuid4

from backend.models.game import Task
from backend.models.assistant import HelpResponse

GRADE_RANGE = "10-12"


MINIGUIDE_SYSTEM_PROMPT = (
    f"You are a friendly math tutor for school students aged {GRADE_RANGE}. "
    "Your ONLY job is to ask ONE short guiding question that nudges the student toward the answer.\n"
    "Rules you must NEVER break:\n"
    "- Do NOT reveal the answer, or any part of it.\n"
    '- Do NOT say "the answer is…", "you should get…", or anything that gives it away.\n'
    "- Do NOT perform the calculation for the student.\n"
    "- Ask exactly one question — concise, age-appropriate, and encouraging.\n"
    "- If the student has shared work, acknowledge what they have done so far before asking your question.\n"
    "- Respond with only the guiding question. No preamble, no explanation."
)

TASK_SYSTEM_PROMPT = (
    f"You are a math task generator for school students aged {GRADE_RANGE}. "
    "Your ONLY job is to generate a single math task appropriate for the given grade and topic.\n"
    "Rules you must NEVER break:\n"
    "- The task must be solvable with a single numeric or fractional answer.\n"
    "- Write the question in English.\n"
    "- Respond with exactly two lines: the first line is the question, the second is the answer.\n"
    "- No explanation, no preamble, no extra lines."
)

HAND_SELECTOR_SYSTEM_PROMPT = (
    f"You are a curriculum planner for a math practice game for school students aged {GRADE_RANGE}. "
    "Your job is to choose which topics and difficulties the student should practice next, "
    "based on their recent performance data and the available topics.\n"
    "Rules you must NEVER break:\n"
    "- Respond with exactly one line per card slot, in the format: TOPIC | DIFFICULTY\n"
    "- DIFFICULTY must be exactly one of: easy, medium, hard\n"
    "- TOPIC must be copied exactly from the provided topic list\n"
    "- Output only the lines, no explanation, no preamble, no extra text\n"
    "Guidelines: "
    "- Prioritise topics where the student is struggling (low accuracy or many hints)\n"
    "- Include a mix of difficulties; avoid all-easy or all-hard hands\n"
    "- If the student has no history, return a balanced mix across topics"
)


def build_guide_user_text(
    question: str,
    context: str,
    has_image: bool,
    profile_context: str = "",
) -> str:
    text = f"Curriculum context:\n{context}\n\nMath task the student is working on:\n{question}\n\n"
    if has_image:
        text += "The student has submitted handwritten work (see image). Please consider it.\n\n"
    if profile_context:
        text += f"{profile_context}\n\n"
    return text


def build_task_text(
    grade: str,
    topic: str,
    difficulty: str,
    curriculum_context: str = "",
    profile_context: str = "",
) -> str:
    text = f"Grade:\n{grade}\n\nTopic:\n{topic}\n\nDifficulty:\n{difficulty}\n\n"
    if curriculum_context:
        text += f"Curriculum context:\n{curriculum_context}\n\n"
    if profile_context:
        text += f"{profile_context}\n\n"
    return text


def build_hand_selector_text(topics: list[str], profile_context: str, hand_size: int) -> str:
    topic_list = "\n".join(f"- {t}" for t in topics)
    text = f"Available topics:\n{topic_list}\n\nNumber of card slots to fill: {hand_size}\n\n"
    if profile_context:
        text += f"{profile_context}\n\n"
    return text


class LLMProvider(ABC):
    """Abstract interface for an LLM backend.

    Implementations must provide:
    - ``guide_student`` - returns a guiding question.
    - ``generate_task`` - generates a single math task for a grade/topic/difficulty.
    - ``select_hand_slots`` - selects the topics and difficulties for questions.
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

    @abstractmethod
    def select_hand_slots(
        self,
        topics: list[str],
        profile_context: str,
        hand_size: int,
    ) -> list[tuple[str, str]]: ...


def _parse_hand_slots(text: str, valid_topics: set[str], hand_size: int) -> list[tuple[str, str]]:
    """Parse LLM output into (topic, difficulty) pairs."""
    valid_difficulties = {"easy", "medium", "hard"}
    slots: list[tuple[str, str]] = []
    for line in text.strip().splitlines():
        line = line.strip()
        if "|" not in line:
            continue
        parts = line.split("|", 1)
        topic = parts[0].strip()
        difficulty = parts[1].strip().lower()
        if topic in valid_topics and difficulty in valid_difficulties:
            slots.append((topic, difficulty))
        if len(slots) == hand_size:
            break
    return slots


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
