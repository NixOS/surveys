import pytest

from nixos_survey_lib.types import Question, SurveySchema


def test_question_construction():
    q = Question(
        id="country",
        prompt="Where do you live?",
        type="single",
        choices=["Africa", "Europe"],
        csv_columns=["Where do you live?"],
    )
    assert q.id == "country"
    assert q.type == "single"
    assert q.choices == ["Africa", "Europe"]


def test_question_text_type_has_no_choices():
    q = Question(
        id="version",
        prompt="Which version?",
        type="text",
        choices=None,
        csv_columns=["Which version?"],
    )
    assert q.choices is None


def test_question_is_frozen():
    q = Question(id="x", prompt="x", type="single", choices=[], csv_columns=[])
    with pytest.raises(Exception):  # FrozenInstanceError
        q.id = "y"


def test_survey_schema_construction():
    q1 = Question(id="a", prompt="A", type="single", choices=["x"], csv_columns=["A"])
    q2 = Question(id="b", prompt="B", type="text", choices=None, csv_columns=["B"])
    s = SurveySchema(title="Test", questions=[q1, q2])
    assert s.title == "Test"
    assert len(s.questions) == 2
