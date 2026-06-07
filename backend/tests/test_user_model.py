from backend.models.user_model import DifficultyRecord, TopicRecord
from backend.services.user_model import UserModel, user_model_to_profile_context


# ---------------------------------------------------------------------------
# UserModel - record_attempt
# ---------------------------------------------------------------------------


class TestRecordAttempt:
    def test_creates_topic_and_difficulty_on_first_attempt(self):
        m = UserModel()
        m.record_attempt("Addition", correct=True, difficulty="easy")
        assert "Addition" in m._topics
        assert "easy" in m._topics["Addition"].records

    def test_increments_attempts(self):
        m = UserModel()
        m.record_attempt("Addition", correct=False, difficulty="easy")
        m.record_attempt("Addition", correct=False, difficulty="easy")
        assert m._topics["Addition"].records["easy"].attempts == 2

    def test_increments_correct_only_when_correct(self):
        m = UserModel()
        m.record_attempt("Addition", correct=True, difficulty="easy")
        m.record_attempt("Addition", correct=False, difficulty="easy")
        rec = m._topics["Addition"].records["easy"]
        assert rec.attempts == 2
        assert rec.correct == 1

    def test_tracks_multiple_difficulties_independently(self):
        m = UserModel()
        m.record_attempt("Multiplikation", correct=True, difficulty="easy")
        m.record_attempt("Multiplikation", correct=False, difficulty="hard")
        easy = m._topics["Multiplikation"].records["easy"]
        hard = m._topics["Multiplikation"].records["hard"]
        assert easy.attempts == 1 and easy.correct == 1
        assert hard.attempts == 1 and hard.correct == 0

    def test_tracks_multiple_topics_independently(self):
        m = UserModel()
        m.record_attempt("Addition", correct=True, difficulty="medium")
        m.record_attempt("Division", correct=False, difficulty="medium")
        assert m._topics["Addition"].records["medium"].correct == 1
        assert m._topics["Division"].records["medium"].correct == 0


# ---------------------------------------------------------------------------
# UserModel - record_hint
# ---------------------------------------------------------------------------


class TestRecordHint:
    def test_creates_record_if_absent(self):
        m = UserModel()
        m.record_hint("Division", difficulty="medium")
        assert "Division" in m._topics
        assert "medium" in m._topics["Division"].records

    def test_increments_hints(self):
        m = UserModel()
        m.record_hint("Division", difficulty="medium")
        m.record_hint("Division", difficulty="medium")
        assert m._topics["Division"].records["medium"].hints == 2

    def test_hints_do_not_affect_attempts_or_correct(self):
        m = UserModel()
        m.record_hint("Division", difficulty="easy")
        rec = m._topics["Division"].records["easy"]
        assert rec.attempts == 0
        assert rec.correct == 0

    def test_hint_on_existing_record_preserves_attempts(self):
        m = UserModel()
        m.record_attempt("Division", correct=True, difficulty="easy")
        m.record_hint("Division", difficulty="easy")
        rec = m._topics["Division"].records["easy"]
        assert rec.attempts == 1
        assert rec.hints == 1


# ---------------------------------------------------------------------------
# UserModel - records property
# ---------------------------------------------------------------------------


class TestRecordsProperty:
    def test_empty_model_returns_empty_list(self):
        assert UserModel().records == []

    def test_returns_one_topic_record_per_topic(self):
        m = UserModel()
        m.record_attempt("Addition", correct=True, difficulty="easy")
        m.record_attempt("Division", correct=False, difficulty="hard")
        topics = {r.topic for r in m.records}
        assert topics == {"Addition", "Division"}

    def test_difficulty_records_nested_correctly(self):
        m = UserModel()
        m.record_attempt("Addition", correct=True, difficulty="easy")
        m.record_attempt("Addition", correct=True, difficulty="medium")
        (topic_rec,) = m.records
        assert set(topic_rec.records.keys()) == {"easy", "medium"}


# ---------------------------------------------------------------------------
# UserModel - get_profile_context (delegates to user_model_to_profile_context)
# ---------------------------------------------------------------------------


class TestGetProfileContext:
    def test_empty_model_returns_empty_string(self):
        assert UserModel().get_profile_context() == ""

    def test_contains_topic_name(self):
        m = UserModel()
        m.record_attempt("Bråk", correct=True, difficulty="easy")
        assert "Bråk" in m.get_profile_context()

    def test_contains_difficulty_breakdown(self):
        m = UserModel()
        m.record_attempt("Addition", correct=True, difficulty="easy")
        m.record_attempt("Addition", correct=False, difficulty="hard")
        ctx = m.get_profile_context()
        assert "easy" in ctx
        assert "hard" in ctx

    def test_correct_slash_attempts_format(self):
        m = UserModel()
        m.record_attempt("Addition", correct=True, difficulty="easy")
        m.record_attempt("Addition", correct=False, difficulty="easy")
        assert "1/2" in m.get_profile_context()

    def test_difficulties_with_zero_attempts_omitted(self):
        m = UserModel()
        m.record_attempt("Addition", correct=True, difficulty="easy")
        ctx = m.get_profile_context()
        assert "medium" not in ctx
        assert "hard" not in ctx

    def test_hint_count_included_in_difficulty_line(self):
        m = UserModel()
        m.record_attempt("Multiplikation", correct=False, difficulty="medium")
        m.record_hint("Multiplikation", difficulty="medium")
        ctx = m.get_profile_context()
        assert "1 hint" in ctx


# ---------------------------------------------------------------------------
# user_model_to_profile_context - standalone function (TopicRecord input)
# ---------------------------------------------------------------------------


class TestUserModelToProfileContext:
    def _make_records(self, topic: str, difficulty: str, attempts: int, correct: int, hints: int) -> list[TopicRecord]:
        return [
            TopicRecord(
                topic=topic,
                records={
                    difficulty: DifficultyRecord(
                        topic=topic,
                        difficulty=difficulty,
                        attempts=attempts,
                        correct=correct,
                        hints=hints,
                    )
                },
            )
        ]

    def test_empty_list_returns_empty_string(self):
        assert user_model_to_profile_context([]) == ""

    def test_all_zero_attempts_returns_empty_string(self):
        records = self._make_records("Addition", "easy", attempts=0, correct=0, hints=0)
        assert user_model_to_profile_context(records) == ""

    def test_contains_topic_name(self):
        records = self._make_records("Bråk", "medium", attempts=2, correct=1, hints=0)
        assert "Bråk" in user_model_to_profile_context(records)

    def test_contains_difficulty(self):
        records = self._make_records("Division", "hard", attempts=1, correct=0, hints=1)
        assert "hard" in user_model_to_profile_context(records)

    def test_correct_slash_attempts_format(self):
        records = self._make_records("Addition", "easy", attempts=3, correct=2, hints=0)
        assert "2/3" in user_model_to_profile_context(records)

    def test_too_easy_label(self):
        # accuracy > 0.8 and hint_rate < 0.2
        records = self._make_records("Addition", "easy", attempts=5, correct=5, hints=0)
        assert "too easy" in user_model_to_profile_context(records)

    def test_too_hard_label(self):
        # accuracy < 0.4
        records = self._make_records("Division", "hard", attempts=5, correct=1, hints=0)
        assert "too hard" in user_model_to_profile_context(records)

    def test_appropriate_difficulty_label(self):
        # accuracy 0.5, hint_rate 0.2
        records = self._make_records("Bråk", "medium", attempts=10, correct=5, hints=2)
        assert "appropriate" in user_model_to_profile_context(records)

    def test_multiple_topics_all_present(self):
        records = [
            TopicRecord(
                topic="Addition",
                records={"easy": DifficultyRecord(topic="Addition", difficulty="easy", attempts=2, correct=2, hints=0)},
            ),
            TopicRecord(
                topic="Division",
                records={"hard": DifficultyRecord(topic="Division", difficulty="hard", attempts=2, correct=0, hints=2)},
            ),
        ]
        ctx = user_model_to_profile_context(records)
        assert "Addition" in ctx
        assert "Division" in ctx

    def test_get_profile_context_delegates_to_standalone(self):
        """UserModel.get_profile_context() and user_model_to_profile_context() must agree."""
        m = UserModel()
        m.record_attempt("Addition", correct=True, difficulty="easy")
        m.record_attempt("Addition", correct=False, difficulty="easy")
        m.record_hint("Addition", difficulty="easy")
        assert m.get_profile_context() == user_model_to_profile_context(m.records)
