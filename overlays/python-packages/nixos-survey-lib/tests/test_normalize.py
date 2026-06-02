import polars as pl

from nixos_survey_lib.normalize import normalize_yes_no
from nixos_survey_lib.types import Question, TextResponse


def _make_text(values: list[str | None]) -> TextResponse:
    q = Question(id="x", prompt="x", type="text", choices=None, csv_columns=["x"])
    return TextResponse(question=q, values=pl.Series(values))


def test_normalize_yes_no_defaults():
    t = _make_text(["yes", "No", "YEP", "nope", "  ", "maybe", ""])
    s = normalize_yes_no(t)
    assert s.values.to_list() == ["Yes", "No", "Yes", "No", "Skipped", "Other", "Skipped"]


def test_normalize_yes_no_question_metadata_preserved():
    t = _make_text(["yes"])
    s = normalize_yes_no(t)
    assert s.question.id == "x"
    assert s.question.type == "single"  # was text, now single


def test_normalize_yes_no_custom_aliases():
    t = _make_text(["si", "no", "ja"])
    s = normalize_yes_no(t, yes_aliases={"si", "ja"}, no_aliases={"no"})
    assert s.values.to_list() == ["Yes", "No", "Yes"]
