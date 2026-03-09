from typing import Any

from backend.models.user_model import DifficultyRecord, TopicRecord


def user_model_to_profile_context(records: list[TopicRecord]) -> str:
    """Build a plain-text LLM context string from a list of TopicRecords."""
    topics = [r for r in records if any(dr.attempts > 0 for dr in r.records.values())]
    if not topics:
        return ""

    lines = ["Student performance profile:"]
    for topic_rec in topics:
        lines.append(f"\n{topic_rec.topic}:")
        for rec in topic_rec.records.values():
            if rec.attempts == 0:
                continue

            accuracy = rec.correct / rec.attempts
            hint_rate = rec.hints / rec.attempts

            if accuracy > 0.8 and hint_rate < 0.2:
                level = "too easy (solving without help)"
            elif accuracy < 0.4:
                level = "too hard (failing most attempts)"
            else:
                level = "appropriate difficulty (learning with support)"

            patterns = []
            if hint_rate > 0.8:
                patterns.append("asks for hints very often")
            if rec.attempts >= 3 and accuracy < 0.3:
                patterns.append("stuck, failing repeatedly")
            if rec.hints == 0 and accuracy > 0.9:
                patterns.append("solving confidently without help")

            pattern_str = f" — {', '.join(patterns)}" if patterns else ""
            lines.append(
                f"\t{rec.difficulty}: {level}, "
                f"{rec.correct}/{rec.attempts} correct, "
                f"{rec.hints} hint(s),{pattern_str}"
            )

    return "\n".join(lines)


class UserModel:
    """Tracks attempts, hints, and correctness per topic and difficulty."""

    def __init__(self, topics: dict[str, TopicRecord] | None = None) -> None:
        self._topics: dict[str, TopicRecord] = topics or {}

    def _get_diff_record(self, topic: str, difficulty: str) -> DifficultyRecord:
        if topic not in self._topics:
            self._topics[topic] = TopicRecord(topic=topic, records={})
        topic_rec = self._topics[topic]
        if difficulty not in topic_rec.records:
            topic_rec.records[difficulty] = DifficultyRecord(topic=topic, difficulty=difficulty)
        return topic_rec.records[difficulty]

    def record_attempt(self, topic: str, correct: bool, difficulty: str) -> None:
        rec = self._get_diff_record(topic, difficulty)
        rec.attempts += 1
        if correct:
            rec.correct += 1

    def record_hint(self, topic: str, difficulty: str) -> None:
        rec = self._get_diff_record(topic, difficulty)
        rec.hints += 1

    @property
    def records(self) -> list[TopicRecord]:
        return list(self._topics.values())

    def get_profile_context(self) -> str:
        return user_model_to_profile_context(self.records)
