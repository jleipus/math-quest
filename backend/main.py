import json
import os
import random
import re
import time
import uuid
from decimal import Decimal, InvalidOperation
from dataclasses import dataclass, field
from html import unescape
from typing import Any, Literal
from urllib.request import Request, urlopen

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from dotenv import load_dotenv
from PIL import Image, ImageDraw
from pydantic import BaseModel
import torch
from torchvision import models


load_dotenv()


Difficulty = Literal["easy", "medium", "hard"]
CardType = Literal["attack", "heal", "shield"]


class Point(BaseModel):
    x: float
    y: float


class Stroke(BaseModel):
    points: list[Point]
    timestamp_ms: int


class HelpRequest(BaseModel):
    session_id: str
    task_id: str
    student_work: list[Stroke] | None = None


class HelpResponse(BaseModel):
    guiding_question: str
    context_used: str


class InitGameRequest(BaseModel):
    grade: str


class InitGameResponse(BaseModel):
    session_id: str
    player_hp: int
    enemy_hp: int
    max_energy: int
    floor: int


class DrawHandRequest(BaseModel):
    session_id: str


class Task(BaseModel):
    task_id: str
    question: str
    grade: str
    topic: str
    difficulty: Difficulty


class Card(BaseModel):
    card_id: str
    card_name: str
    card_power: int
    card_type: CardType
    energy_cost: int
    task: Task


class DrawHandResponse(BaseModel):
    hand: list[Card]
    enemy_next_damage: int


class EndTurnRequest(BaseModel):
    session_id: str


class EndTurnResponse(BaseModel):
    player_hp: int
    enemy_damage: int
    shield_absorbed: int
    hand: list[Card]
    enemy_next_damage: int
    enemy_hp: int
    enemy_max_hp: int


class AnswerRequest(BaseModel):
    session_id: str
    task_id: str
    answer: str


class AnswerResponse(BaseModel):
    correct: bool
    card_id: str
    message: str


class PlayCardRequest(BaseModel):
    session_id: str
    card_id: str


class PlayCardResponse(BaseModel):
    enemy_hp: int
    player_hp: int
    effect_value: int
    card_type: CardType
    enemy_defeated: bool


class DifficultyRecord(BaseModel):
    topic: str
    difficulty: str
    attempts: int
    hints: int
    correct: int


class TopicRecord(BaseModel):
    topic: str
    records: dict[str, DifficultyRecord]


class UserModelResponse(BaseModel):
    session_id: str
    topics: list[TopicRecord]


class GeneratedCardSpec(BaseModel):
    card_name: str
    card_type: CardType
    card_power: int
    energy_cost: int
    topic: str
    difficulty: Difficulty
    question: str
    answer: str


@dataclass
class TaskData:
    task_id: str
    question: str
    answer: str
    grade: str
    topic: str
    difficulty: Difficulty


@dataclass
class CardData:
    card_id: str
    card_name: str
    card_power: int
    card_type: CardType
    energy_cost: int
    task: TaskData


@dataclass
class SessionState:
    session_id: str
    grade: str
    player_hp: int = 30
    player_max_hp: int = 30
    enemy_hp: int = 40
    enemy_max_hp: int = 40
    floor: int = 1
    max_energy: int = 3
    shield: int = 0
    hand: list[CardData] = field(default_factory=list)
    solved_card_ids: set[str] = field(default_factory=set)
    next_enemy_damage: int = 7
    tasks_by_id: dict[str, TaskData] = field(default_factory=dict)
    task_to_card: dict[str, str] = field(default_factory=dict)
    user_model: dict[str, dict[str, dict[str, int]]] = field(default_factory=dict)


HF_BASE_URL = "https://router.huggingface.co/v1"
HF_MODEL = "AI-Sweden-Models/Llama-3-8B-instruct:featherless-ai"
HF_TOKEN = "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"
GRADE_MATTEBOKEN_URLS: dict[str, str] = {
    "Grade 4": "https://www.matteboken.se/lektioner/mellanstadiet/skolar-4",
    "Grade 5": "https://www.matteboken.se/lektioner/mellanstadiet/skolar-5",
    "Grade 6": "https://www.matteboken.se/lektioner/mellanstadiet/skolar-6",
}
MATTEBOKEN_TOPIC_CACHE: dict[str, tuple[str, ...]] = {}

CNN_READY = False
CNN_INIT_ERROR: str | None = None
CNN_MODEL: Any = None
CNN_PREPROCESS: Any = None
CNN_LABELS: list[str] = []

try:
    cnn_weights = models.ResNet18_Weights.DEFAULT
    CNN_MODEL = models.resnet18(weights=cnn_weights)
    CNN_MODEL.eval()
    CNN_PREPROCESS = cnn_weights.transforms()
    CNN_LABELS = list(cnn_weights.meta.get("categories", []))
    CNN_READY = True
except Exception as exc:
    CNN_INIT_ERROR = str(exc)


def normalize_answer(raw: str) -> str:
    return "".join(raw.lower().strip().split())


def _parse_numeric_answer(raw: str) -> Decimal | None:
    value = normalize_answer(raw)
    if not value:
        return None

    if value.endswith("%"):
        number = _parse_numeric_answer(value[:-1])
        if number is None:
            return None
        return number / Decimal("100")

    if re.fullmatch(r"-?\d+/\d+", value):
        numerator_text, denominator_text = value.split("/", 1)
        denominator = int(denominator_text)
        if denominator == 0:
            return None
        return Decimal(int(numerator_text)) / Decimal(denominator)

    decimal_candidate = value.replace(",", ".")
    if re.fullmatch(r"-?\d+(?:\.\d+)?", decimal_candidate):
        try:
            return Decimal(decimal_candidate)
        except InvalidOperation:
            return None

    return None


def answers_match(given: str, expected: str) -> bool:
    normalized_given = normalize_answer(given)
    normalized_expected = normalize_answer(expected)
    if normalized_given == normalized_expected:
        return True

    given_number = _parse_numeric_answer(given)
    expected_number = _parse_numeric_answer(expected)
    if given_number is None or expected_number is None:
        return False

    return abs(given_number - expected_number) <= Decimal("0.000001")


def parse_allowed_origins(raw_value: str | None) -> list[str]:
    if raw_value is None:
        return []

    value = raw_value.strip()
    if not value:
        return []

    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return [part.strip() for part in value.split(",") if part.strip()]

    if isinstance(parsed, list):
        return [str(item).strip() for item in parsed if str(item).strip()]
    if isinstance(parsed, str):
        parsed_value = parsed.strip()
        return [parsed_value] if parsed_value else []

    return []


def _strip_html_tags(raw_html: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", raw_html)
    unescaped = unescape(without_tags)
    return re.sub(r"\s+", " ", unescaped).strip()


def _normalize_topic_label(label: str) -> str:
    cleaned = re.sub(r"^årskurs\s*\d+\s*[–-]\s*", "", label, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def _is_noise_topic_label(label: str) -> bool:
    lowered = label.lower().strip(" :")
    if not lowered:
        return True

    blocked_exact = {
        "matteboken",
        "meny",
        "logga in",
        "registrera",
        "cookie",
        "integritet",
        "kontakt",
        "om oss",
        "startsida",
        "mellanstadiet",
        "lågstadiet",
        "högstadiet",
        "gymnasiet",
        "översikt",
        "nästa avsnitt",
    }
    if lowered in blocked_exact:
        return True

    blocked_contains = (
        "nästa avsnitt",
        "föregående avsnitt",
        "översikt",
        "cookie",
        "integritet",
        "marknadsföring",
        "besöksstatistik",
    )
    if any(term in lowered for term in blocked_contains):
        return True

    return False


def _extract_topics_from_matteboken_html(raw_html: str) -> tuple[str, ...]:
    patterns = [
        r"<h2[^>]*>(.*?)</h2>",
        r"<h3[^>]*>(.*?)</h3>",
        r"<a[^>]*href=\"/lektioner/mellanstadiet/skolar-\d+/[^\"]+\"[^>]*>(.*?)</a>",
    ]

    seen: set[str] = set()
    topics: list[str] = []
    for pattern in patterns:
        for match in re.findall(pattern, raw_html, flags=re.IGNORECASE | re.DOTALL):
            cleaned = _normalize_topic_label(_strip_html_tags(match))
            lowered = cleaned.lower()
            if not cleaned or len(cleaned) < 3 or len(cleaned) > 70:
                continue
            if _is_noise_topic_label(cleaned):
                continue
            if not re.search(r"[a-zåäö]", lowered):
                continue
            if lowered in seen:
                continue
            seen.add(lowered)
            topics.append(cleaned)
            if len(topics) >= 12:
                return tuple(topics)

    return tuple(topics)


def get_grade_topic_hints(grade: str) -> tuple[str, ...]:
    cached = MATTEBOKEN_TOPIC_CACHE.get(grade)
    if cached is not None:
        return cached

    source_url = GRADE_MATTEBOKEN_URLS.get(grade)
    if not source_url:
        raise RuntimeError(f"Unknown grade: {grade}")

    try:
        request = Request(source_url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(request, timeout=8) as response:
            html = response.read().decode("utf-8", errors="ignore")
        extracted = _extract_topics_from_matteboken_html(html)
        if len(extracted) < 4:
            raise RuntimeError(f"Too few topics extracted from Matteboken for {grade}")
    except Exception as exc:
        raise RuntimeError(f"Failed to fetch Matteboken topics for {grade}: {exc}") from exc

    MATTEBOKEN_TOPIC_CACHE[grade] = extracted
    return extracted


def to_card_model(card: CardData) -> Card:
    return Card(
        card_id=card.card_id,
        card_name=card.card_name,
        card_power=card.card_power,
        card_type=card.card_type,
        energy_cost=card.energy_cost,
        task=Task(
            task_id=card.task.task_id,
            question=card.task.question,
            grade=card.task.grade,
            topic=card.task.topic,
            difficulty=card.task.difficulty,
        ),
    )


def _extract_json_text(raw: str) -> str:
    text = raw.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1).strip()
    return text


def _strokes_to_image(strokes: list[Stroke], size: int = 224, margin: int = 14) -> Image.Image:
    image = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(image)

    all_points: list[Point] = []
    for stroke in strokes:
        all_points.extend(stroke.points)

    if not all_points:
        return image

    min_x = min(point.x for point in all_points)
    max_x = max(point.x for point in all_points)
    min_y = min(point.y for point in all_points)
    max_y = max(point.y for point in all_points)

    span_x = max(max_x - min_x, 1.0)
    span_y = max(max_y - min_y, 1.0)
    scale = min((size - 2 * margin) / span_x, (size - 2 * margin) / span_y)

    def project(point: Point) -> tuple[float, float]:
        x = margin + (point.x - min_x) * scale
        y = margin + (point.y - min_y) * scale
        return x, y

    for stroke in strokes:
        if len(stroke.points) == 1:
            x, y = project(stroke.points[0])
            draw.ellipse((x - 2, y - 2, x + 2, y + 2), fill="black")
            continue

        projected = [project(point) for point in stroke.points]
        draw.line(projected, fill="black", width=4, joint="curve")

    return image


def extract_cnn_drawing_summary(student_work: list[Stroke] | None) -> dict[str, Any]:
    strokes = student_work or []
    point_count = sum(len(stroke.points) for stroke in strokes)
    if not strokes or point_count == 0:
        return {
            "has_drawing": False,
            "stroke_count": len(strokes),
            "point_count": point_count,
        }

    if not CNN_READY:
        return {
            "has_drawing": True,
            "stroke_count": len(strokes),
            "point_count": point_count,
            "cnn_ready": False,
            "cnn_error": CNN_INIT_ERROR,
        }

    image = _strokes_to_image(strokes)
    tensor = CNN_PREPROCESS(image).unsqueeze(0)
    with torch.no_grad():
        logits = CNN_MODEL(tensor).squeeze(0)

    probs = torch.softmax(logits, dim=0)
    top_k = torch.topk(probs, k=3)
    top_predictions = []
    for score, index in zip(top_k.values.tolist(), top_k.indices.tolist()):
        label = CNN_LABELS[index] if 0 <= index < len(CNN_LABELS) else f"class_{index}"
        top_predictions.append({"label": label, "prob": round(float(score), 4)})

    return {
        "has_drawing": True,
        "stroke_count": len(strokes),
        "point_count": point_count,
        "cnn_ready": True,
        "top_predictions": top_predictions,
    }


def _to_int(value: Any, default: int) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        match = re.search(r"-?\d+", value)
        if match:
            return int(match.group(0))
    return default


def _build_hint_task_context(task: TaskData) -> str:
    question = task.question.strip()
    lowered = question.lower()
    numbers = re.findall(r"\d+(?:[\.,]\d+)?", question)

    if "lös för x" in lowered or ("=" in question and "x" in lowered):
        return f"Equation with variable x. Expression text: {question}."

    if "%" in question or "procent" in lowered:
        nums = ", ".join(numbers) if numbers else "none"
        return f"Percentage problem. Values present: {nums}."

    fraction_match = re.search(r"(\d+\s*/\s*\d+)", question)
    if fraction_match:
        frac = fraction_match.group(1).replace(" ", "")
        target = numbers[-1] if numbers else "unknown"
        return f"Fraction-of-number problem. Fraction: {frac}. Target number: {target}."

    if "omkrets" in lowered and "cirkel" in lowered:
        radius = numbers[-1] if numbers else "unknown"
        return f"Circle circumference problem with radius {radius}."

    if numbers:
        return f"Word problem in topic {task.topic}. Difficulty {task.difficulty}. " f"Relevant values: {', '.join(numbers)}."

    return f"Word problem in topic {task.topic}. Difficulty {task.difficulty}."


def _normalize_card_candidate(item: dict[str, Any]) -> dict[str, Any]:
    key_aliases = {
        "name": "card_name",
        "card": "card_name",
        "namn": "card_name",
        "kortnamn": "card_name",
        "kort_namn": "card_name",
        "type": "card_type",
        "typ": "card_type",
        "korttyp": "card_type",
        "kort_typ": "card_type",
        "power": "card_power",
        "styrka": "card_power",
        "kortkraft": "card_power",
        "kort_kraft": "card_power",
        "energy": "energy_cost",
        "energycost": "energy_cost",
        "energy_cost": "energy_cost",
        "energikostnad": "energy_cost",
        "energi_kostnad": "energy_cost",
        "ämne": "topic",
        "subject": "topic",
        "svårighetsgrad": "difficulty",
        "difficulty": "difficulty",
        "fråga": "question",
        "svar": "answer",
    }

    normalized: dict[str, Any] = {}
    for raw_key, value in item.items():
        lowered = str(raw_key).strip().lower()
        target_key = key_aliases.get(lowered, lowered)
        normalized[target_key] = value

    card_type_raw = str(normalized.get("card_type", "")).strip().lower()
    card_type_map = {
        "attack": "attack",
        "damage": "attack",
        "heal": "heal",
        "healing": "heal",
        "shield": "shield",
        "skydd": "shield",
        "defend": "shield",
        "defense": "shield",
    }
    normalized["card_type"] = card_type_map.get(card_type_raw, card_type_raw)

    difficulty_raw = str(normalized.get("difficulty", "")).strip().lower()
    difficulty_map = {
        "easy": "easy",
        "latt": "easy",
        "lätt": "easy",
        "medium": "medium",
        "medel": "medium",
        "hard": "hard",
        "svår": "hard",
        "hård": "hard",
        "svar": "hard",
    }
    normalized["difficulty"] = difficulty_map.get(difficulty_raw, difficulty_raw)

    normalized["card_name"] = str(normalized.get("card_name", "")).strip()
    normalized["topic"] = str(normalized.get("topic", "")).strip()
    normalized["question"] = str(normalized.get("question", "")).strip()
    normalized["answer"] = str(normalized.get("answer", "")).strip()
    normalized["card_power"] = _to_int(normalized.get("card_power"), 8)
    normalized["energy_cost"] = _to_int(normalized.get("energy_cost"), 1)

    return normalized


def generate_llm_cards(grade: str) -> list[GeneratedCardSpec]:
    token = HF_TOKEN
    if not token:
        raise RuntimeError("HF_TOKEN is missing")

    if grade not in GRADE_MATTEBOKEN_URLS:
        raise RuntimeError(f"Unknown grade: {grade}")
    source_url = GRADE_MATTEBOKEN_URLS[grade]
    allowed_topics = get_grade_topic_hints(grade)
    topics_text = ", ".join(allowed_topics) if allowed_topics else "grade-appropriate middle school topics"

    client = OpenAI(base_url=HF_BASE_URL, api_key=token)
    prompt = (
        "Create exactly 3 math cards for a turn-based game. "
        f"Use Matteboken as curriculum source for this grade: {source_url}. "
        f"Keep topics aligned to this grade. Prefer only these topics: {topics_text}. "
        'Return ONLY valid JSON in the format: {"cards":[...]} with no markdown. '
        "Cards must include one of each difficulty: easy, medium, hard. "
        "Each card must include fields: card_name, card_type, card_power, energy_cost, "
        "topic, difficulty, question, answer. "
        "Rules: card_type must be attack/heal/shield, card_power 4-14, energy_cost 1-2. "
        "answer must be short and exact (for string comparison). "
        f"Target grade level: {grade}. "
        "Never refuse, never add explanations, never add extra keys."
    )

    completion = client.chat.completions.create(
        model=HF_MODEL,
        messages=[
            {"role": "system", "content": "You return strict JSON and nothing else."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=700,
        response_format={"type": "json_object"},
    )

    content = completion.choices[0].message.content
    if not content:
        raise RuntimeError("Model returned empty content")

    payload = json.loads(_extract_json_text(content))
    cards_raw: Any
    if isinstance(payload, dict) and "cards" in payload:
        cards_raw = payload["cards"]
    elif isinstance(payload, dict) and "kort" in payload:
        cards_raw = payload["kort"]
    elif isinstance(payload, list):
        cards_raw = payload
    else:
        raise RuntimeError("Model JSON missing cards array")

    if not isinstance(cards_raw, list):
        raise RuntimeError("Model cards field is not a list")

    cards: list[GeneratedCardSpec] = []
    for item in cards_raw:
        if not isinstance(item, dict):
            continue
        normalized_item = _normalize_card_candidate(item)
        try:
            cards.append(GeneratedCardSpec.model_validate(normalized_item))
        except Exception:
            continue

    if len(cards) < 3:
        raise RuntimeError("Model returned fewer than 3 cards")

    by_diff: dict[Difficulty, GeneratedCardSpec] = {}
    for card in cards:
        if card.difficulty not in by_diff:
            by_diff[card.difficulty] = card

    missing = [d for d in ("easy", "medium", "hard") if d not in by_diff]
    if missing:
        raise RuntimeError(f"Model did not provide all required difficulties: {missing}")

    return [by_diff["easy"], by_diff["medium"], by_diff["hard"]]


def generate_llm_hint(task: TaskData, attempts: int, hints: int, student_work: list[Stroke] | None) -> str:
    token = HF_TOKEN
    if not token:
        return f"What is the first small step to solve this {task.topic.lower()} task?"

    drawing_cnn_summary = extract_cnn_drawing_summary(student_work)
    task_context = _build_hint_task_context(task)

    client = OpenAI(base_url=HF_BASE_URL, api_key=token)
    prompt = (
        "Skriv EN kort sokratisk ledfråga på svenska för elevens första steg (max 20 ord).\n"
        "Hårda regler:\n"
        "1) Du får INTE återge uppgiftens formulering.\n"
        "2) Du får INTE ställa samma fråga som uppgiften.\n"
        "3) Du får INTE använda generiska frågor som 'Vad är 2+2?'.\n"
        "4) Frågan måste peka på första operationen/delsteget.\n"
        "5) Frågan ska innehålla minst en konkret detalj från task context (tal, symbol eller term).\n"
        "6) Svara med EN fråga och inget annat.\n\n"
        "7) Frågan måste börja med någon av dessa starter: 'Hur kan du', 'Vilket första steg', "
        "'Vilken operation', 'Vad gör du först', 'Kan du börja med'.\n"
        "8) Frågan får INTE börja med 'Vad är'.\n\n"
        "Exempel bra:\n"
        "Uppgift: Vad är 50% av 10?\n"
        "Ledfråga: Hur kan du skriva 50% som decimaltal innan du multiplicerar med 10?\n\n"
        "Uppgift: Lös för x: 3x + 7 = 31\n"
        "Ledfråga: Vilken operation gör du först på båda sidor för att få bort +7?\n\n"
        "Exempel dåligt:\n"
        "Uppgift: Vad är 50% av 10?\n"
        "Ledfråga: Vad är 50% av 10?\n\n"
        f"Grade: {task.grade}\n"
        f"Topic: {task.topic}\n"
        f"Difficulty: {task.difficulty}\n"
        f"Task context: {task_context}\n"
        f"Attempts so far: {attempts}\n"
        f"Hints used so far: {hints}\n"
        f"Student provided drawing work: {'yes' if drawing_cnn_summary.get('has_drawing') else 'no'}\n"
        "Student drawing CNN summary (weak signal only): "
        f"{json.dumps(drawing_cnn_summary, ensure_ascii=False)}"
    )

    completion = client.chat.completions.create(
        model=HF_MODEL,
        messages=[
            {
                "role": "system",
                "content": ("Du är en strikt svensk mattelärare som skriver ledfrågor. " "Du får aldrig upprepa uppgiftstexten ordagrant. " "Skriv bara en fråga för första delsteget."),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
        max_tokens=70,
    )
    content = completion.choices[0].message.content
    if not content:
        return f"What is the first small step to solve this {task.topic.lower()} task?"
    return content.strip()


class GameStore:
    def __init__(self) -> None:
        self.sessions: dict[str, SessionState] = {}

    def grades(self) -> list[str]:
        return list(GRADE_MATTEBOKEN_URLS.keys())

    def get_session(self, session_id: str) -> SessionState:
        session = self.sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Unknown session_id")
        return session

    def create_session(self, grade: str) -> SessionState:
        if grade not in GRADE_MATTEBOKEN_URLS:
            raise HTTPException(status_code=400, detail="Unknown grade")
        session_id = str(uuid.uuid4())
        enemy_hp = 40
        session = SessionState(
            session_id=session_id,
            grade=grade,
            enemy_hp=enemy_hp,
            enemy_max_hp=enemy_hp,
            next_enemy_damage=random.randint(6, 9),
        )
        self.sessions[session_id] = session
        return session

    def draw_hand(self, session: SessionState) -> DrawHandResponse:
        generated: list[GeneratedCardSpec] | None = None
        last_error: Exception | None = None
        for attempt in range(1, 4):
            try:
                generated = generate_llm_cards(session.grade)
                break
            except Exception as exc:
                last_error = exc
                print(f"LLM card generation failed (attempt {attempt}/3): {exc}")
                if attempt < 3:
                    time.sleep(0.35 * attempt)

        if generated is None:
            raise HTTPException(status_code=502, detail="Kunde inte generera kort med LLM just nu") from last_error

        random.shuffle(generated)

        cards: list[CardData] = []
        next_tasks_by_id: dict[str, TaskData] = {}
        next_task_to_card: dict[str, str] = {}
        for generated_card in generated:
            task_id = str(uuid.uuid4())
            card_id = str(uuid.uuid4())
            task = TaskData(
                task_id=task_id,
                question=generated_card.question.strip(),
                answer=generated_card.answer.strip(),
                grade=session.grade,
                topic=generated_card.topic.strip(),
                difficulty=generated_card.difficulty,
            )
            card = CardData(
                card_id=card_id,
                card_name=generated_card.card_name.strip() or "Card",
                card_power=max(1, min(20, int(generated_card.card_power))),
                card_type=generated_card.card_type,
                energy_cost=max(1, min(3, int(generated_card.energy_cost))),
                task=task,
            )
            cards.append(card)
            next_tasks_by_id[task_id] = task
            next_task_to_card[task_id] = card_id

        session.hand = cards
        session.solved_card_ids.clear()
        session.tasks_by_id = next_tasks_by_id
        session.task_to_card = next_task_to_card
        session.next_enemy_damage = random.randint(6, 10 + session.floor)
        return DrawHandResponse(
            hand=[to_card_model(card) for card in session.hand],
            enemy_next_damage=session.next_enemy_damage,
        )

    def _user_model_record(self, session: SessionState, task: TaskData) -> dict[str, int]:
        topic_bucket = session.user_model.setdefault(task.topic, {})
        diff_bucket = topic_bucket.setdefault(
            task.difficulty,
            {"attempts": 0, "hints": 0, "correct": 0},
        )
        return diff_bucket

    def submit_answer(self, session: SessionState, task_id: str, answer: str) -> AnswerResponse:
        task = session.tasks_by_id.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Unknown task_id for this session")

        record = self._user_model_record(session, task)
        record["attempts"] += 1
        card_id = session.task_to_card[task_id]
        if answers_match(answer, task.answer):
            session.solved_card_ids.add(card_id)
            record["correct"] += 1
            return AnswerResponse(correct=True, card_id=card_id, message="Correct! You can now play this card.")

        return AnswerResponse(correct=False, card_id=card_id, message="Not quite. Try again or ask for a hint.")

    def help(self, session: SessionState, task_id: str, student_work: list[Stroke] | None) -> HelpResponse:
        task = session.tasks_by_id.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Unknown task_id for this session")

        record = self._user_model_record(session, task)
        record["hints"] += 1
        try:
            guiding_question = generate_llm_hint(
                task=task,
                attempts=record["attempts"],
                hints=record["hints"],
                student_work=student_work,
            )
        except Exception as exc:
            print(f"LLM hint generation failed: {exc}")
            guiding_question = f"What is the first small step to solve this {task.topic.lower()} task?"

        return HelpResponse(
            guiding_question=guiding_question,
            context_used=f"{task.grade} · {task.topic} · {task.difficulty}",
        )

    def play_card(self, session: SessionState, card_id: str) -> PlayCardResponse:
        card = next((entry for entry in session.hand if entry.card_id == card_id), None)
        if not card:
            raise HTTPException(status_code=404, detail="Card not in hand")

        if card_id not in session.solved_card_ids:
            raise HTTPException(status_code=400, detail="Solve the task before playing this card")

        if card.card_type == "attack":
            session.enemy_hp = max(0, session.enemy_hp - card.card_power)
            effect = card.card_power
        elif card.card_type == "heal":
            before = session.player_hp
            session.player_hp = min(session.player_max_hp, session.player_hp + card.card_power)
            effect = session.player_hp - before
        else:
            session.shield += card.card_power
            effect = card.card_power

        session.hand = [entry for entry in session.hand if entry.card_id != card_id]
        session.solved_card_ids.discard(card_id)
        enemy_defeated = session.enemy_hp <= 0

        return PlayCardResponse(
            enemy_hp=session.enemy_hp,
            player_hp=session.player_hp,
            effect_value=effect,
            card_type=card.card_type,
            enemy_defeated=enemy_defeated,
        )

    def end_turn(self, session: SessionState) -> EndTurnResponse:
        if session.enemy_hp <= 0:
            session.floor += 1
            session.enemy_max_hp = 35 + (session.floor * 7)
            session.enemy_hp = session.enemy_max_hp
            draw = self.draw_hand(session)
            return EndTurnResponse(
                player_hp=session.player_hp,
                enemy_damage=0,
                shield_absorbed=0,
                hand=draw.hand,
                enemy_next_damage=draw.enemy_next_damage,
                enemy_hp=session.enemy_hp,
                enemy_max_hp=session.enemy_max_hp,
            )

        incoming = session.next_enemy_damage
        absorbed = min(session.shield, incoming)
        taken = max(0, incoming - absorbed)
        session.player_hp = max(0, session.player_hp - taken)
        session.shield = 0

        draw = self.draw_hand(session)
        return EndTurnResponse(
            player_hp=session.player_hp,
            enemy_damage=incoming,
            shield_absorbed=absorbed,
            hand=draw.hand,
            enemy_next_damage=draw.enemy_next_damage,
            enemy_hp=session.enemy_hp,
            enemy_max_hp=session.enemy_max_hp,
        )

    def user_model_response(self, session: SessionState) -> UserModelResponse:
        topics: list[TopicRecord] = []
        for topic_name, records in sorted(session.user_model.items()):
            topic_records: dict[str, DifficultyRecord] = {}
            for difficulty_name, stats in records.items():
                topic_records[difficulty_name] = DifficultyRecord(
                    topic=topic_name,
                    difficulty=difficulty_name,
                    attempts=stats["attempts"],
                    hints=stats["hints"],
                    correct=stats["correct"],
                )
            topics.append(TopicRecord(topic=topic_name, records=topic_records))

        return UserModelResponse(session_id=session.session_id, topics=topics)


store = GameStore()

app = FastAPI(title="DAIS Active Learning Backend", version="1.0.0")

allowed_origins_raw = parse_allowed_origins(os.getenv("DAIS_ALLOWED_ORIGINS"))
allowed_origins = sorted(
    {
        *allowed_origins_raw,
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/curriculum/grades")
def get_grades() -> dict[str, list[str]]:
    return {"grades": store.grades()}


@app.post("/api/v1/game/init", response_model=InitGameResponse)
def init_game(payload: InitGameRequest) -> InitGameResponse:
    session = store.create_session(payload.grade)
    return InitGameResponse(
        session_id=session.session_id,
        player_hp=session.player_hp,
        enemy_hp=session.enemy_hp,
        max_energy=session.max_energy,
        floor=session.floor,
    )


@app.post("/api/v1/game/draw", response_model=DrawHandResponse)
def draw_hand(payload: DrawHandRequest) -> DrawHandResponse:
    session = store.get_session(payload.session_id)
    return store.draw_hand(session)


@app.post("/api/v1/game/answer", response_model=AnswerResponse)
def submit_answer(payload: AnswerRequest) -> AnswerResponse:
    session = store.get_session(payload.session_id)
    return store.submit_answer(session, payload.task_id, payload.answer)


@app.post("/api/v1/agent/help", response_model=HelpResponse)
def request_help(payload: HelpRequest) -> HelpResponse:
    session = store.get_session(payload.session_id)
    return store.help(session, payload.task_id, payload.student_work)


@app.post("/api/v1/game/play_card", response_model=PlayCardResponse)
def play_card(payload: PlayCardRequest) -> PlayCardResponse:
    session = store.get_session(payload.session_id)
    return store.play_card(session, payload.card_id)


@app.post("/api/v1/game/end_turn", response_model=EndTurnResponse)
def end_turn(payload: EndTurnRequest) -> EndTurnResponse:
    session = store.get_session(payload.session_id)
    return store.end_turn(session)


@app.get("/api/v1/user_model/{session_id}", response_model=UserModelResponse)
def user_model(session_id: str) -> UserModelResponse:
    session = store.get_session(session_id)
    return store.user_model_response(session)
