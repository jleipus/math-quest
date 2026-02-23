import random
from fractions import Fraction
from threading import Lock
from uuid import UUID, uuid4

from backend.config import get_settings
from backend.models.game import Card, CardType, Task, InitGameResponse, DrawHandResponse, NextFloorResponse


_DIFFICULTIES = ["easy", "medium", "hard"]

# Card names grouped by type so themed names can be chosen
_ATTACK_NAMES = [
    "Fireball",
    "Ice Lance",
    "Thunder Strike",
    "Shadow Bolt",
    "Dragon Breath",
    "Arcane Missile",
    "Poison Dart",
    "Lava Burst",
    "Chain Lightning",
    "Void Rift",
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
    "medium": (11, 20),
    "hard": (21, 35),
}


class GameSession:
    def __init__(
        self,
        session_id: UUID,
        player_hp: int,
        enemy_hp: int,
        topic: str,
    ) -> None:
        self.session_id = session_id
        self.player_hp = player_hp
        self.enemy_hp = enemy_hp
        self.enemy_max_hp = enemy_hp
        self.topic = topic
        self.floor: int = 1
        self.hand: list[Card] = []
        self.shield: int = 0  # absorbed damage for the next enemy attack
        self.enemy_next_damage: int = 0  # pre-rolled damage shown to player
        self._task_to_card: dict[str, str] = {}
        self._expected_answers: dict[str, str] = {}

    def set_hand(self, hand: list[Card]) -> None:
        self.hand = hand
        self._rebuild_task_map()

    def _rebuild_task_map(self) -> None:
        self._task_to_card = {str(card.task.task_id): str(card.card_id) for card in self.hand}

    def register_answer(self, task_id: str, expected_answer: str) -> None:
        self._expected_answers[task_id] = expected_answer

    def get_expected_answer(self, task_id: str) -> str | None:
        return self._expected_answers.get(task_id)

    def get_card_for_task(self, task_id: str) -> Card | None:
        card_id = self._task_to_card.get(task_id)
        if card_id is None:
            return None
        return next((c for c in self.hand if str(c.card_id) == card_id), None)

    def get_card(self, card_id: str) -> Card | None:
        return next((c for c in self.hand if str(c.card_id) == card_id), None)

    def unlock_card(self, card_id: str) -> None:
        for card in self.hand:
            if str(card.card_id) == card_id:
                card.locked = False
                return

    def remove_card(self, card_id: str) -> None:
        self.hand = [c for c in self.hand if str(c.card_id) != card_id]
        self._rebuild_task_map()


class GameService:
    def __init__(self) -> None:
        self._lock = Lock()
        self._sessions: dict[str, GameSession] = {}
        self._rng = random.Random()

    def init_game(self, topic: str) -> tuple[InitGameResponse, GameSession]:
        settings = get_settings()
        session_id = uuid4()

        session = GameSession(
            session_id=session_id,
            player_hp=settings.player_start_hp,
            enemy_hp=settings.enemy_start_hp,
            topic=topic,
        )

        with self._lock:
            self._sessions[str(session_id)] = session

        return (
            InitGameResponse(
                session_id=session_id,
                player_hp=session.player_hp,
                enemy_hp=session.enemy_hp,
                floor=session.floor,
            ),
            session,
        )

    def get_session(self, session_id: str) -> GameSession | None:
        with self._lock:
            return self._sessions.get(session_id)

    def draw_hand(self, session: GameSession, hand_size: int) -> DrawHandResponse:
        hand, expected_answers = self._generate_hand(session.topic, hand_size)
        session.set_hand(hand)
        for task_id, answer in expected_answers.items():
            session.register_answer(task_id, answer)
        # Pre-roll the enemy's upcoming attack so the player can see it
        if session.enemy_next_damage == 0:
            session.enemy_next_damage = self._rng.randint(10, 20)
        return DrawHandResponse(hand=hand, enemy_next_damage=session.enemy_next_damage)

    def _generate_hand(self, topic: str, hand_size: int) -> tuple[list[Card], dict[str, str]]:
        from backend.services.llm import llm_service, task_registry

        # Generate tasks with mixed difficulties
        tasks_per_difficulty = self._spread_difficulties(hand_size)
        all_tasks: list[Task] = []
        for difficulty, count in tasks_per_difficulty.items():
            if count == 0:
                continue
            tasks = llm_service.generate_tasks(topic=topic, difficulty=difficulty, count=count)
            all_tasks.extend(tasks)
        task_registry.put_many(all_tasks)
        self._rng.shuffle(all_tasks)

        expected_answers: dict[str, str] = {}
        hand: list[Card] = []

        # Build card types: 1 attack + 1 heal + 1 shield guaranteed,
        # remaining slots filled with attack or shield only (max 1 heal per hand).
        guaranteed: list[CardType] = ["attack", "heal", "shield"]
        extra_count = len(all_tasks) - len(guaranteed)
        extra_types: list[CardType] = self._rng.choices(["attack", "shield"], k=max(0, extra_count))
        card_types: list[CardType] = guaranteed + extra_types
        self._rng.shuffle(card_types)

        for task, card_type in zip(all_tasks, card_types):
            power_low, power_high = _POWER_BY_DIFFICULTY.get(task.difficulty, (10, 20))
            card_power = self._rng.randint(power_low, power_high)

            if card_type == "attack":
                card_name = self._rng.choice(_ATTACK_NAMES)
            elif card_type == "heal":
                card_name = self._rng.choice(_HEAL_NAMES)
            else:
                card_name = self._rng.choice(_SHIELD_NAMES)

            card = Card(
                card_id=uuid4(),
                card_name=card_name,
                card_power=card_power,
                card_type=card_type,
                locked=True,
                task=Task(
                    task_id=task.task_id,
                    question=task.question,
                    topic=task.topic,
                    difficulty=task.difficulty,
                    expected_answer=task.expected_answer,
                ),
            )
            expected_answers[str(task.task_id)] = task.expected_answer
            hand.append(card)

        return hand, expected_answers

    def _spread_difficulties(self, hand_size: int) -> dict[str, int]:
        """Distribute hand_size tasks roughly evenly across easy/medium/hard."""
        counts: dict[str, int] = {d: 0 for d in _DIFFICULTIES}
        for i in range(hand_size):
            counts[_DIFFICULTIES[i % len(_DIFFICULTIES)]] += 1
        return counts

    def enemy_attack(self, session: GameSession) -> tuple[int, int, int]:
        """
        Resolve enemy attack for the current turn using the pre-rolled damage.

        Returns (new_player_hp, raw_damage, shield_absorbed).
        The shield is consumed entirely after each attack.
        """
        raw_damage = session.enemy_next_damage or self._rng.randint(10, 20)

        absorbed = min(session.shield, raw_damage)
        actual_damage = raw_damage - absorbed
        session.shield = 0  # shield consumed
        session.player_hp = max(0, session.player_hp - actual_damage)

        # Pre-roll next turn's damage
        session.enemy_next_damage = self._rng.randint(10, 20)
        return session.player_hp, raw_damage, absorbed

    def next_floor(self, session: GameSession) -> NextFloorResponse:
        """
        Advance to the next floor after the current enemy is defeated.
        Enemy HP and damage scale with the floor number.
        """
        session.floor += 1
        # Each floor the enemy gets ~20% more HP, minimum 20 extra
        base_hp = get_settings().enemy_start_hp
        new_hp = int(base_hp * (1.2 ** (session.floor - 1)))
        session.enemy_hp = new_hp
        session.enemy_max_hp = new_hp

        # Damage scales similarly: base range raised by 3 per floor
        floor_bonus = (session.floor - 1) * 3
        session.enemy_next_damage = self._rng.randint(10 + floor_bonus, 20 + floor_bonus)

        return NextFloorResponse(
            floor=session.floor,
            enemy_hp=new_hp,
            enemy_max_hp=new_hp,
            enemy_next_damage=session.enemy_next_damage,
        )

    def apply_card(self, session: GameSession, card: Card) -> tuple[int, int]:
        """
        Apply a card's effect.

        Returns (new_enemy_hp, new_player_hp).
        """
        if card.card_type == "attack":
            session.enemy_hp = max(0, session.enemy_hp - card.card_power)
        elif card.card_type == "heal":
            settings = get_settings()
            session.player_hp = min(settings.player_start_hp, session.player_hp + card.card_power)
        elif card.card_type == "shield":
            session.shield += card.card_power

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
