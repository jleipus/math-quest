import random
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from backend.config import get_settings
from backend.models.game import Card, CardType, AttackSubtype, Task
from backend.models.user_model import TopicRecord
from backend.services.consts import (
    _ATTACK_SUBTYPES,
    _HEAL_NAMES,
    _SHIELD_NAMES,
    _POWER_BY_DIFFICULTY,
    _ENERGY_BY_DIFFICULTY,
)


def generate_hand(
    grade: str,
    uid: str | None = None,
    hand_size: int | None = None,
    client_user_model: list[TopicRecord] | None = None,
) -> list[Card]:
    from backend.services.llm import llm_service
    from backend.services.curriculum import curriculum_service
    from backend.services.user_model import user_model_to_profile_context

    settings = get_settings()
    if hand_size is None:
        hand_size = settings.default_hand_size

    rng = random.Random()

    profile_context = ""
    if uid:
        from backend.services.firestore_user_model import firestore_user_model_service

        user_model = firestore_user_model_service.get_or_create(uid)
        profile_context = user_model.get_profile_context()
    elif client_user_model:
        profile_context = user_model_to_profile_context(client_user_model)

    grade_topics = curriculum_service.get_all_topics(grade)

    # If user model is not empty, LLM picks topics and difficulties for hand
    slots: list[tuple[str, str]] = []
    if len(profile_context) > 0:
        slots = llm_service.select_hand_slots(
            topics=grade_topics,
            profile_context=profile_context,
            hand_size=hand_size,
            session_id=uid or "anonymous",
        )

    # Fallback if insufficient pairings are generated, or UM is empty
    fallback_difficulties = ["easy", "easy", "medium", "medium", "hard"]
    while len(slots) < hand_size:
        topic = rng.choice(grade_topics)
        difficulty = fallback_difficulties[len(slots) % len(fallback_difficulties)]
        slots.append((topic, difficulty))

    # Group pairings by topic to reduce number of LLM requests
    topic_to_difficulties: dict[str, list[str]] = defaultdict(list)
    for topic, difficulty in slots:
        topic_to_difficulties[topic].append(difficulty)

    # Thread worker
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
            session_id=uid or "anonymous",
        )

    unique_topics = list(topic_to_difficulties.keys())
    with ThreadPoolExecutor(max_workers=len(unique_topics)) as executor:
        futures_map = {
            topic: executor.submit(topic_worker, topic, topic_to_difficulties[topic]) for topic in unique_topics
        }

    all_tasks: list[Task] = []
    for topic, future in futures_map.items():
        tasks = future.result()
        for task in tasks:
            all_tasks.append(task)

    rng.shuffle(all_tasks)

    # Assign card types: 2 attack + 1 heal + 1 shield + 1 random (attack|shield)
    guaranteed_types: list[CardType] = ["attack", "attack", "heal", "shield"]
    extra_type: list[CardType] = [rng.choice(["attack", "shield"])]
    card_types = guaranteed_types + extra_type
    rng.shuffle(card_types)

    hand: list[Card] = []
    for task, card_type in zip(all_tasks, card_types):
        # Select randomized power range by difficulty
        power_low, power_high = _POWER_BY_DIFFICULTY.get(task.difficulty, (10, 20))

        # Pick randomized name by card type
        attack_subtype: AttackSubtype | None = None
        if card_type == "attack":
            attack_subtype, name_pool = rng.choice(_ATTACK_SUBTYPES)
            card_name = rng.choice(name_pool)
        elif card_type == "heal":
            card_name = rng.choice(_HEAL_NAMES)
        else:
            card_name = rng.choice(_SHIELD_NAMES)

        hand.append(
            Card(
                card_id=str(uuid4()),
                card_name=card_name,
                card_power=rng.randint(power_low, power_high),
                card_type=card_type,
                attack_subtype=attack_subtype,
                energy_cost=_ENERGY_BY_DIFFICULTY.get(task.difficulty, 1),
                task=Task(
                    task_id=task.task_id,
                    question=task.question,
                    grade=task.grade,
                    topic=task.topic,
                    difficulty=task.difficulty,
                    expected_answer=task.expected_answer,
                ),
            )
        )

    return hand
