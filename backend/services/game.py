import math
import random
import time
from collections import OrderedDict, defaultdict
from contextlib import contextmanager
from fractions import Fraction
from threading import Lock
from typing import Generator
from uuid import UUID, uuid4
from concurrent.futures import ThreadPoolExecutor

from backend.config import get_settings
from backend.models.game import Card, CardType, AttackSubtype, Task, InitGameResponse, DrawHandResponse


# Card names grouped by attack subtype
_MAGIC_NAMES = [
    "Fireball",
    "Ice Lance",
    "Shadow Bolt",
    "Arcane Missile",
    "Lava Burst",
    "Void Rift",
    "Frost Nova",
    "Chain Lightning",
]

_BOW_NAMES = [
    "Poison Dart",
    "Eagle Eye",
    "Piercing Shot",
    "Volley",
    "Snipe",
    "Hunters Mark",
]

_SWORD_NAMES = [
    "Thunder Strike",
    "Dragon Breath",
    "Slash",
    "Riposte",
    "Whirlwind",
    "Cleave",
]

_AXE_NAMES = [
    "Skull Splitter",
    "Ravage",
    "Headbutt",
    "Reckless Swing",
    "Bloodlust",
    "Brutal Strike",
]

_ATTACK_SUBTYPES: list[tuple[AttackSubtype, list[str]]] = [
    ("magic", _MAGIC_NAMES),
    ("bow", _BOW_NAMES),
    ("sword", _SWORD_NAMES),
    ("axe", _AXE_NAMES),
]

_HEAL_NAMES = [
    "Holy Light",
    "Mending Touch",
    "Nature's Grasp",
    "Sacred Bloom",
    "Regenerate",
]

_SHIELD_NAMES = [
    "Stone Wall",
    "Iron Aegis",
    "Frost Ward",
    "Barrier",
    "Bulwark",
]

# (low, high) attack / heal / shield power by difficulty
_POWER_BY_DIFFICULTY: dict[str, tuple[int, int]] = {
    "easy": (5, 10),
    "medium": (11, 25),
    "hard": (26, 40),
}

# Energy cost per difficulty
_ENERGY_BY_DIFFICULTY: dict[str, int] = {
    "easy": 1,
    "medium": 2,
    "hard": 3,
}


class GameSession:
    def __init__(
        self,
        session_id: UUID,
        player_hp: int,
        enemy_hp: int,
        grade: str,
    ) -> None:
        self.session_id = session_id
        self.player_hp = player_hp
        self.enemy_hp = enemy_hp
        self.enemy_max_hp = enemy_hp
        self.grade = grade
        self.floor: int = 1
        self.hand: list[Card] = []
        self.shield: int = 0  # absorbed damage for the next enemy attack
        self.enemy_next_damage: int = 0  # pre-rolled damage for next attack
        self._task_to_card: dict[str, str] = {}
        self._expected_answers: dict[str, str] = {}
        self._tasks: dict[str, Task] = {}  # full Task objects, keyed by task_id
        self._wrong_attempts: dict[str, int] = {}  # card_id -> wrong attempt count
        # Each session gets its own RNG so concurrent sessions don't interfere
        self._rng = random.Random()
        # Per-session lock to guard against concurrent requests on the same session
        self._lock = Lock()

    def set_hand(self, hand: list[Card]) -> None:
        self.hand = hand
        self._rebuild_task_map()

    def _rebuild_task_map(self) -> None:
        self._task_to_card = {str(card.task.task_id): str(card.card_id) for card in self.hand}

    def set_answer(self, task_id: str, expected_answer: str) -> None:
        self._expected_answers[task_id] = expected_answer

    def get_expected_answer(self, task_id: str) -> str | None:
        return self._expected_answers.get(task_id)

    def store_task(self, task: Task) -> None:
        self._tasks[str(task.task_id)] = task

    def get_task(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    def get_card_for_task(self, task_id: str) -> Card | None:
        card_id = self._task_to_card.get(task_id)
        if card_id is None:
            return None
        return next((c for c in self.hand if str(c.card_id) == card_id), None)

    def get_card(self, card_id: str) -> Card | None:
        return next((c for c in self.hand if str(c.card_id) == card_id), None)

    def remove_card(self, card_id: str) -> None:
        self.hand = [c for c in self.hand if str(c.card_id) != card_id]
        self._rebuild_task_map()

    def record_wrong_attempt(self, card_id: str) -> None:
        """Increment the wrong-attempt counter for a card."""
        self._wrong_attempts[card_id] = self._wrong_attempts.get(card_id, 0) + 1

    def penalised_power(self, card: Card) -> int:
        """Return card_power reduced by 10% per wrong attempt, capped at 50% reduction."""
        base = card.card_power
        wrongs = min(self._wrong_attempts.get(str(card.card_id), 0), 5)
        reduction = math.ceil(base * 0.10) * wrongs
        return max(base - reduction, math.ceil(base * 0.50))


_MAX_SESSIONS = 100
_SESSION_TTL = 60 * 60 * 2  # 2 hours


class GameService:
    def __init__(self) -> None:
        self._lock = Lock()
        self._sessions: OrderedDict[str, GameSession] = OrderedDict()
        self._session_last_active: dict[str, float] = {}

    def _evict(self) -> None:
        """Evict expired sessions, then oldest if still over cap. Caller must hold _lock."""
        now = time.monotonic()
        expired = [sid for sid, t in self._session_last_active.items() if now - t > _SESSION_TTL]
        for sid in expired:
            self._sessions.pop(sid, None)
            self._session_last_active.pop(sid, None)

        while len(self._sessions) >= _MAX_SESSIONS:
            sid, _ = self._sessions.popitem(last=False)
            self._session_last_active.pop(sid, None)

    def init_game(self, grade: str) -> tuple[InitGameResponse, GameSession]:
        settings = get_settings()
        session_id = uuid4()

        session = GameSession(
            session_id=session_id,
            player_hp=settings.player_start_hp,
            enemy_hp=settings.enemy_start_hp,
            grade=grade,
        )

        with self._lock:
            self._evict()
            self._sessions[str(session_id)] = session
            self._session_last_active[str(session_id)] = time.monotonic()

        return (
            InitGameResponse(
                session_id=session_id,
                player_hp=session.player_hp,
                enemy_hp=session.enemy_hp,
                max_energy=settings.max_energy,
                floor=session.floor,
            ),
            session,
        )

    def get_session(self, session_id: str) -> GameSession | None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is not None:
                self._session_last_active[session_id] = time.monotonic()
                self._sessions.move_to_end(session_id)
            return session

    def get_task(self, session_id: str, task_id: str) -> "Task | None":
        """Return the Task stored on a session, or None if not found."""
        session = self.get_session(session_id)
        if session is None:
            return None
        return session.get_task(task_id)

    @contextmanager
    def get_session_locked(self, session_id: str) -> Generator[GameSession | None, None, None]:
        """Context manager that returns the session while holding its per-session lock."""
        session = self.get_session(session_id)
        if session is None:
            yield None
            return
        with session._lock:
            yield session

    def draw_hand(self, session: GameSession, hand_size: int) -> DrawHandResponse:
        # Clear previous round's task data before generating new hand
        session._tasks.clear()
        session._expected_answers.clear()

        # Generate new cards
        hand, expected_answers = self._generate_hand(session, hand_size)
        session.set_hand(hand)

        # Set answers for cards
        for task_id, answer in expected_answers.items():
            session.set_answer(task_id, answer)

        # Pre-determine damage for enemy
        if session.enemy_next_damage == 0:
            session.enemy_next_damage = session._rng.randint(10, 20)

        return DrawHandResponse(hand=hand, enemy_next_damage=session.enemy_next_damage)

    def _generate_hand(self, session: GameSession, hand_size: int) -> tuple[list[Card], dict[str, str]]:
        from backend.services.llm import llm_service
        from backend.services.curriculum import curriculum_service
        from backend.services.user_model import user_model_service

        grade = session.grade
        sid = str(session.session_id)
        user_model = user_model_service.get_or_create(sid)
        profile_context = user_model.get_profile_context()

        grade_topics = curriculum_service.get_all_topics(grade)

        # If user model is not empty, let the LLM pick topics and difficulties
        slots = []
        if len(user_model.records) > 0:
            slots = llm_service.select_hand_slots(
                topics=grade_topics,
                profile_context=profile_context,
                hand_size=hand_size,
                session_id=sid,
            )

        # Fallback: fill any missing slots with random topic + balanced difficulties
        fallback_difficulties = ["easy", "easy", "medium", "medium", "hard"]
        while len(slots) < hand_size:
            topic = session._rng.choice(grade_topics)
            difficulty = fallback_difficulties[len(slots) % len(fallback_difficulties)]
            slots.append((topic, difficulty))

        # Group slots by topic so all cards for the same topic are generated in one LLM call.
        topic_to_difficulties: dict[str, list[str]] = defaultdict(list)

        # Track original slot order so we can restore it after parallel generation.
        slot_indices: dict[str, list[int]] = defaultdict(list)
        for idx, (topic, difficulty) in enumerate(slots):
            topic_to_difficulties[topic].append(difficulty)
            slot_indices[topic].append(idx)

        def topic_worker(topic: str, difficulties: list[str]) -> list[Task]:
            try:
                curriculum_context = curriculum_service.retrieve_context(grade=grade, topic=topic, question=topic)
            except RuntimeError:
                curriculum_context = ""

            return llm_service.generate_tasks_for_topic(
                grade=grade,
                topic=topic,
                difficulties=difficulties,
                curriculum_context=curriculum_context,
                profile_context=profile_context,
                session_id=sid,
            )

        unique_topics = list(topic_to_difficulties.keys())
        with ThreadPoolExecutor(max_workers=len(unique_topics)) as executor:
            futures_map = {
                topic: executor.submit(topic_worker, topic, topic_to_difficulties[topic]) for topic in unique_topics
            }

        # Reconstruct all_tasks in original slot order.
        all_tasks: list[Task] = [None] * len(slots)  # type: ignore[list-item]
        for topic, future in futures_map.items():
            tasks = future.result()
            indices = slot_indices[topic]
            for i, task in zip(indices, tasks):
                all_tasks[i] = task
                session.store_task(task)

        # Drop any slots the LLM failed to fill
        all_tasks = [t for t in all_tasks if t is not None]

        session._rng.shuffle(all_tasks)

        expected_answers: dict[str, str] = {}
        hand: list[Card] = []

        # Build card types:
        # 2 attack + 1 heal + 1 shield guaranteed
        guaranteed_types: list[CardType] = ["attack", "attack", "heal", "shield"]
        # 1 card either attack or shield at random
        extra_type: list[CardType] = [session._rng.choice(["attack", "shield"])]

        card_types = guaranteed_types + extra_type
        session._rng.shuffle(card_types)

        for task, card_type in zip(all_tasks, card_types):
            power_low, power_high = _POWER_BY_DIFFICULTY.get(task.difficulty, (10, 20))
            card_power = session._rng.randint(power_low, power_high)

            attack_subtype: AttackSubtype | None = None
            if card_type == "attack":
                attack_subtype, name_pool = session._rng.choice(_ATTACK_SUBTYPES)
                card_name = session._rng.choice(name_pool)
            elif card_type == "heal":
                card_name = session._rng.choice(_HEAL_NAMES)
            else:
                card_name = session._rng.choice(_SHIELD_NAMES)

            energy_cost = _ENERGY_BY_DIFFICULTY.get(task.difficulty, 1)
            card = Card(
                card_id=uuid4(),
                card_name=card_name,
                card_power=card_power,
                card_type=card_type,
                attack_subtype=attack_subtype,
                energy_cost=energy_cost,
                task=Task(
                    task_id=task.task_id,
                    question=task.question,
                    grade=task.grade,
                    topic=task.topic,
                    difficulty=task.difficulty,
                    expected_answer=task.expected_answer,
                ),
            )
            expected_answers[str(task.task_id)] = task.expected_answer
            hand.append(card)

        return hand, expected_answers

    def enemy_attack(self, session: GameSession) -> tuple[int, int, int]:
        """Resolve enemy attack for end-of-turn."""
        if session.enemy_hp <= 0:
            self._advance_floor(session)
            session.shield = 0
            return session.player_hp, 0, 0

        raw_damage = session.enemy_next_damage or session._rng.randint(10, 20)
        absorbed = min(session.shield, raw_damage)
        actual_damage = raw_damage - absorbed
        session.shield = 0
        session.player_hp = max(0, session.player_hp - actual_damage)

        # Pre-roll next turn's damage
        session.enemy_next_damage = session._rng.randint(10, 20)
        return session.player_hp, raw_damage, absorbed

    def _advance_floor(self, session: GameSession) -> None:
        """Advance to the next floor, increase enemy HP and damage, and flush the user model."""
        from backend.services.user_model import user_model_service

        session.floor += 1
        base_hp = get_settings().enemy_start_hp
        new_hp = int(base_hp * (1.2 ** (session.floor - 1)))
        session.enemy_hp = new_hp
        session.enemy_max_hp = new_hp

        floor_bonus = (session.floor - 1) * 3
        session.enemy_next_damage = session._rng.randint(10 + floor_bonus, 20 + floor_bonus)

        user_model_service.flush(str(session.session_id))

    def apply_card(self, session: GameSession, card: Card) -> tuple[int, int]:
        """Apply a card's effect using the penalised power."""
        power = session.penalised_power(card)
        if card.card_type == "attack":
            session.enemy_hp = max(0, session.enemy_hp - power)
        elif card.card_type == "heal":
            settings = get_settings()
            session.player_hp = min(settings.player_start_hp, session.player_hp + power)
        elif card.card_type == "shield":
            session.shield += power

        return session.enemy_hp, session.player_hp

    @staticmethod
    def check_answer(submitted: str, expected: str) -> bool:
        submitted = submitted.strip()
        expected = expected.strip()

        if submitted.lower() == expected.lower():
            return True

        try:
            sub_frac = Fraction(submitted.replace(",", "."))
            exp_frac = Fraction(expected.replace(",", "."))
            if sub_frac == exp_frac:
                return True
        except (ValueError, ZeroDivisionError):
            pass

        try:
            sub_float = float(submitted.replace(",", "."))
            exp_float = float(expected.replace(",", "."))
            if abs(sub_float - exp_float) < 1e-6:
                return True
        except ValueError:
            pass

        return False


game_service = GameService()
