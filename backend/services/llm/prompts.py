GUIDANCE_SYSTEM_PROMPT = """
You are a friendly math tutor for school students aged 10-12.
Your ONLY job is to ask ONE short, age-appropriate, guiding question that nudges the student toward the answer.

NEVER reveal the answer, or any part of it.
NEVER say "the answer is", "you should get", or anything that gives the answer away.
NEVER perform the calculation for the student.
ALWAYS respond in English.

Respond with a JSON object and nothing else.
Do not include markdown fences, preamble, or any text outside the JSON object.
Schema: {"guiding_question": "<your single guiding question>"}
"""

TASK_SYSTEM_PROMPT = """
You are a math task generator for school students aged 10-12.
You will be given a topic, a curriculum context, and a list of difficulties to generate tasks for.
Generate one distinct ENGLISH math task per requested difficulty, in the order listed.

The answer to each question should be a single number or fraction.
All tasks must cover the same topic but use different numbers, scenarios, or phrasings, no duplicates.
Follow the curriculum context as a guide for appropriate level.
Questions MUST be in English.

Respond with a JSON object and nothing else.
Do not include markdown fences, preamble, or any text outside the JSON object.
Schema: {"tasks": [{"difficulty": "<difficulty>", "question": "<question>", "answer": "<answer>"}, ...]}
"""

HAND_SELECTOR_SYSTEM_PROMPT = """
You are a curriculum planner for a math practice game for school students aged 10-12.
Your job is to choose which topics and difficulties the student should practice next,
based on their recent performance data and the available topics.

DIFFICULTY must be exactly one of: easy, medium, hard
TOPIC must be copied exactly from the provided topic list
Prioritise topics where the student is struggling (low accuracy or many hints)
Include a mix of difficulties; avoid all-easy or all-hard hands

Respond with a JSON object and nothing else.
Do not include markdown fences, preamble, or any text outside the JSON object.
The array must contain exactly as many entries as the requested number of card slots.
Schema: {"slots": [{"topic": "<topic>", "difficulty": "<difficulty>"}, ...]}
"""


def build_guide_user_text(
    question: str,
    context: str,
    has_image: bool,
    profile_context: str = "",
    previous_questions: list[str] | None = None,
) -> str:
    text = f"""Curriculum context:\n{context}\n\nMath task the student is working on:\n{question}\n\n"""
    if has_image:
        text += "Consider the students submitted handwritten work (see image).\n\n"
    if profile_context:
        text += f"Student profile:\n{profile_context}\n\n"
    if previous_questions:
        history = "\n".join(f"- {q}" for q in previous_questions)
        text += f"Previous guiding questions already given to this student:\n{history}\n\n"
    return text


def build_task_text(
    grade: str,
    topic: str,
    difficulties: list[str],
    curriculum_context: str = "",
    profile_context: str = "",
) -> str:
    difficulties_str = ", ".join(difficulties)
    text = f"Grade:\n{grade}\n\nTopic:\n{topic}\n\nDifficulties (generate one task each, in this order):\n{difficulties_str}\n\n"
    if curriculum_context:
        text += f"Curriculum context:\n{curriculum_context}\n\n"
    if profile_context:
        text += f"Student profile:\n{profile_context}\n\n"
    return text


def build_hand_selector_text(topics: list[str], profile_context: str, hand_size: int) -> str:
    topic_list = "\n".join(f"- {t}" for t in topics)
    text = f"Available topics:\n{topic_list}\n\nNumber of card slots to fill: {hand_size}\n\n"
    if profile_context:
        text += f"{profile_context}\n\n"
    return text
