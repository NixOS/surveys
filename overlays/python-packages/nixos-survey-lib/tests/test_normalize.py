import polars as pl

from nixos_survey_lib.normalize import extract_first_semver, normalize_yes_no
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


def test_extract_first_semver_extracts_canonical():
    t = _make_text(["2.18.5", "  2.24.1  ", "v3.0.0", "nix 1.2.3 release"])
    s = extract_first_semver(t)
    assert s.values.to_list() == ["2.18.5", "2.24.1", "3.0.0", "1.2.3"]


def test_extract_first_semver_skipped_for_empty():
    t = _make_text(["", "   ", None])
    s = extract_first_semver(t)
    assert s.values.to_list() == ["Skipped", "Skipped", "Skipped"]


def test_extract_first_semver_no_match_label():
    t = _make_text(["not a version", "main"])
    s = extract_first_semver(t)
    assert s.values.to_list() == ["No Match", "No Match"]
