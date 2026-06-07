import pytest

from backend.services.llm.base import (
    _extract_json,
    _parse_guidance,
    _parse_hand_slots,
    _parse_tasks,
)


class TestExtractJson:
    def test_extracts_object_amid_surrounding_text(self):
        assert _extract_json('prose {"a": 1} trailing') == {"a": 1}

    def test_extracts_outermost_braces(self):
        assert _extract_json('{"a": {"b": 2}}') == {"a": {"b": 2}}

    def test_raises_when_no_object(self):
        with pytest.raises(RuntimeError):
            _extract_json("no json here")

    def test_raises_on_invalid_json(self):
        with pytest.raises(RuntimeError):
            _extract_json("{not valid}")


class TestParseGuidance:
    def test_returns_trimmed_question(self):
        assert _parse_guidance('{"guiding_question": "  Vad blir 2+2?  "}') == "Vad blir 2+2?"

    def test_raises_when_missing(self):
        with pytest.raises(RuntimeError):
            _parse_guidance('{"other": "x"}')

    def test_raises_when_empty(self):
        with pytest.raises(RuntimeError):
            _parse_guidance('{"guiding_question": "   "}')


class TestParseTasks:
    def test_parses_valid_task(self):
        raw = '{"tasks": [{"difficulty": "easy", "question": "1+1?", "answer": "2"}]}'
        (task,) = _parse_tasks(raw, grade="Skolår 4", topic="Addition")
        assert task.question == "1+1?"
        assert task.expected_answer == "2"
        assert task.difficulty == "easy"
        assert task.grade == "Skolår 4"
        assert task.topic == "Addition"
        assert task.task_id  # a uuid is assigned

    def test_normalises_difficulty_case(self):
        raw = '{"tasks": [{"difficulty": "EASY", "question": "q", "answer": "a"}]}'
        assert _parse_tasks(raw, grade="g", topic="t")[0].difficulty == "easy"

    def test_skips_invalid_and_empty_entries(self):
        raw = (
            '{"tasks": ['
            '{"difficulty": "trivial", "question": "q", "answer": "a"},'  # bad difficulty
            '{"difficulty": "easy", "question": "", "answer": "a"},'  # empty question
            '{"difficulty": "hard", "question": "q2", "answer": "a2"}]}'
        )
        assert [t.difficulty for t in _parse_tasks(raw, grade="g", topic="t")] == ["hard"]

    def test_raises_when_no_valid_tasks(self):
        raw = '{"tasks": [{"difficulty": "easy", "question": "", "answer": "a"}]}'
        with pytest.raises(RuntimeError):
            _parse_tasks(raw, grade="g", topic="t")

    def test_defaults_answer_type_to_number(self):
        raw = '{"tasks": [{"difficulty": "easy", "question": "q", "answer": "2"}]}'
        task = _parse_tasks(raw, grade="g", topic="t")[0]
        assert task.answer_type == "number"
        assert task.accepted_answers == []

    def test_parses_text_answer_type_and_accepted_answers(self):
        raw = (
            '{"tasks": [{"difficulty": "easy", "question": "Vad heter figuren?",'
            ' "answer": "triangel", "answer_type": "text",'
            ' "accepted_answers": ["triangel", "triangeln", ""]}]}'
        )
        task = _parse_tasks(raw, grade="g", topic="t")[0]
        assert task.answer_type == "text"
        assert task.accepted_answers == ["triangel", "triangeln"]  # blanks dropped

    def test_unknown_answer_type_falls_back_to_number(self):
        raw = '{"tasks": [{"difficulty": "easy", "question": "q", "answer": "2", "answer_type": "essay"}]}'
        assert _parse_tasks(raw, grade="g", topic="t")[0].answer_type == "number"


class TestParseHandSlots:
    def test_filters_to_valid_topics_and_difficulties(self):
        raw = (
            '{"slots": ['
            '{"topic": "Addition", "difficulty": "easy"},'
            '{"topic": "Unknown", "difficulty": "easy"},'  # not a valid topic
            '{"topic": "Division", "difficulty": "trivial"}]}'  # not a valid difficulty
        )
        slots = _parse_hand_slots(raw, valid_topics={"Addition", "Division"}, hand_size=5)
        assert slots == [("Addition", "easy")]

    def test_caps_at_hand_size(self):
        raw = (
            '{"slots": ['
            '{"topic": "A", "difficulty": "easy"},'
            '{"topic": "A", "difficulty": "medium"},'
            '{"topic": "A", "difficulty": "hard"}]}'
        )
        assert len(_parse_hand_slots(raw, valid_topics={"A"}, hand_size=2)) == 2
