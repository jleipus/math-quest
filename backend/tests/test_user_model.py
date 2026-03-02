import os
import tempfile

import pytest

from backend.models.user_model import DifficultyRecord, TopicRecord
from backend.services.user_model import UserModel, UserModelService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _svc_with_tmp_db() -> tuple[UserModelService, str]:
    """Return a UserModelService backed by a temporary TinyDB file."""
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp.close()
    svc = UserModelService()
    # Point the service at the temp file by pre-opening the DB.
    from tinydb import TinyDB

    svc._db = TinyDB(tmp.name)
    return svc, tmp.name


# ---------------------------------------------------------------------------
# UserModel — record_attempt
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
# UserModel — record_hint
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
# UserModel — records property
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
# UserModel — get_profile_context
# ---------------------------------------------------------------------------


class TestGetProfileContext:
    def test_empty_model_returns_empty_string(self):
        assert UserModel().get_profile_context() == ""

    def test_contains_topic_name(self):
        m = UserModel()
        m.record_attempt("Bråk", correct=True, difficulty="easy")
        assert "Bråk" in m.get_profile_context()

    def test_contains_aggregated_totals(self):
        m = UserModel()
        m.record_attempt("Addition", correct=True, difficulty="easy")
        m.record_attempt("Addition", correct=False, difficulty="medium")
        ctx = m.get_profile_context()
        assert "2 attempts" in ctx
        assert "1 correct" in ctx

    def test_contains_difficulty_breakdown(self):
        m = UserModel()
        m.record_attempt("Addition", correct=True, difficulty="easy")
        m.record_attempt("Addition", correct=False, difficulty="hard")
        ctx = m.get_profile_context()
        assert "easy" in ctx
        assert "hard" in ctx

    def test_struggling_note_when_hints_gte_attempts(self):
        m = UserModel()
        m.record_attempt("Division", correct=False, difficulty="hard")
        m.record_hint("Division", difficulty="hard")
        assert "struggling" in m.get_profile_context()

    def test_no_struggling_note_when_hints_less_than_attempts(self):
        m = UserModel()
        m.record_attempt("Division", correct=True, difficulty="easy")
        m.record_attempt("Division", correct=True, difficulty="easy")
        m.record_hint("Division", difficulty="easy")
        assert "struggling" not in m.get_profile_context()

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
# UserModel — serialisation round-trip
# ---------------------------------------------------------------------------


class TestSerialisation:
    def test_to_dict_empty(self):
        assert UserModel().to_dict() == {}

    def test_round_trip_single_record(self):
        m = UserModel()
        m.record_attempt("Addition", correct=True, difficulty="easy")
        m.record_hint("Addition", difficulty="easy")
        restored = UserModel.from_dict(m.to_dict())
        rec = restored._topics["Addition"].records["easy"]
        assert rec.attempts == 1
        assert rec.correct == 1
        assert rec.hints == 1

    def test_round_trip_multiple_topics_and_difficulties(self):
        m = UserModel()
        m.record_attempt("Division", correct=False, difficulty="hard")
        m.record_attempt("Bråk", correct=True, difficulty="medium")
        m.record_hint("Bråk", difficulty="medium")
        restored = UserModel.from_dict(m.to_dict())
        assert restored._topics["Division"].records["hard"].attempts == 1
        assert restored._topics["Bråk"].records["medium"].correct == 1
        assert restored._topics["Bråk"].records["medium"].hints == 1

    def test_from_dict_empty(self):
        m = UserModel.from_dict({})
        assert m.records == []


# ---------------------------------------------------------------------------
# UserModelService — in-memory behaviour
# ---------------------------------------------------------------------------


class TestUserModelService:
    def test_get_or_create_returns_new_model(self):
        svc = UserModelService()
        model = svc.get_or_create("session-1")
        assert isinstance(model, UserModel)

    def test_get_or_create_returns_same_instance(self):
        svc = UserModelService()
        a = svc.get_or_create("session-1")
        b = svc.get_or_create("session-1")
        assert a is b

    def test_different_sessions_are_isolated(self):
        svc = UserModelService()
        svc.record_attempt("session-1", "Addition", correct=True, difficulty="easy")
        model2 = svc.get_or_create("session-2")
        assert model2.records == []

    def test_state_persists_across_calls(self):
        svc = UserModelService()
        svc.record_attempt("session-1", "Division", correct=False, difficulty="hard")
        model = svc.get_or_create("session-1")
        assert model._topics["Division"].records["hard"].attempts == 1

    def test_record_hint_via_service(self):
        svc = UserModelService()
        svc.record_hint("session-1", "Bråk", difficulty="medium")
        model = svc.get_or_create("session-1")
        assert model._topics["Bråk"].records["medium"].hints == 1


# ---------------------------------------------------------------------------
# UserModelService — TinyDB persistence
# ---------------------------------------------------------------------------


class TestUserModelServicePersistence:
    def test_attempt_survives_service_restart(self):
        svc, path = _svc_with_tmp_db()
        try:
            svc.record_attempt("s1", "Addition", correct=True, difficulty="easy")

            # Simulate restart: new service instance pointed at same DB file
            svc2 = UserModelService()
            from tinydb import TinyDB

            svc2._db = TinyDB(path)

            model = svc2.get_or_create("s1")
            assert model._topics["Addition"].records["easy"].attempts == 1
            assert model._topics["Addition"].records["easy"].correct == 1
        finally:
            os.unlink(path)

    def test_hint_survives_service_restart(self):
        svc, path = _svc_with_tmp_db()
        try:
            svc.record_hint("s1", "Division", difficulty="hard")

            svc2 = UserModelService()
            from tinydb import TinyDB

            svc2._db = TinyDB(path)

            model = svc2.get_or_create("s1")
            assert model._topics["Division"].records["hard"].hints == 1
        finally:
            os.unlink(path)

    def test_multiple_sessions_stored_independently(self):
        svc, path = _svc_with_tmp_db()
        try:
            svc.record_attempt("s1", "Addition", correct=True, difficulty="easy")
            svc.record_attempt("s2", "Division", correct=False, difficulty="hard")

            svc2 = UserModelService()
            from tinydb import TinyDB

            svc2._db = TinyDB(path)

            m1 = svc2.get_or_create("s1")
            m2 = svc2.get_or_create("s2")
            assert "Addition" in m1._topics
            assert "Division" in m2._topics
            assert "Division" not in m1._topics
            assert "Addition" not in m2._topics
        finally:
            os.unlink(path)

    def test_incremental_updates_accumulate(self):
        svc, path = _svc_with_tmp_db()
        try:
            svc.record_attempt("s1", "Bråk", correct=False, difficulty="medium")
            svc.record_attempt("s1", "Bråk", correct=True, difficulty="medium")
            svc.record_hint("s1", "Bråk", difficulty="medium")

            svc2 = UserModelService()
            from tinydb import TinyDB

            svc2._db = TinyDB(path)

            rec = svc2.get_or_create("s1")._topics["Bråk"].records["medium"]
            assert rec.attempts == 2
            assert rec.correct == 1
            assert rec.hints == 1
        finally:
            os.unlink(path)

    def test_unknown_session_returns_fresh_model(self):
        svc, path = _svc_with_tmp_db()
        try:
            model = svc.get_or_create("unknown-session")
            assert model.records == []
        finally:
            os.unlink(path)
