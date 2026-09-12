"""Tests for the dataclasses and response containers in nixos_survey_lib.types.

Question and Survey now come from schema.py; this module checks the shapes
the rest of the pipeline relies on, not the TOML rules (see test_schema.py).
"""

import pytest
from nixos_survey_lib.schema import Group, GroupText, LanguageTexts, Privacy, QuestionText
from nixos_survey_lib.types import Question, Survey


def _survey(questions: list[Question]) -> Survey:
    """Minimal single-language Survey wrapping ``questions`` in one group.

    Tests of Responses only need something with a ``.questions`` list, but
    Survey has no optional fields, so this builds the smallest valid one.
    """
    texts = LanguageTexts(
        language="en",
        title="t",
        intro="i",
        end=None,
        groups={"g": GroupText(title="G", description=None)},
        questions={
            q.id: QuestionText(prompt=q.prompt, help=None, choices=q.choices) for q in questions
        },
    )
    return Survey(
        id=2,
        language="en",
        languages=["en"],
        privacy=Privacy(
            anonymized=True,
            save_ip_address=False,
            save_referrer=False,
            date_stamp=False,
            save_timings=False,
        ),
        groups=[Group(id="g", title="G", description=None, questions=questions)],
        title="t",
        intro="i",
        end=None,
        texts={"en": texts},
    )


def test_question_construction():
    """The original five keyword fields still construct a Question."""
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
    """Text questions carry ``choices=None``; the loader relies on None,
    not an empty list, to tell the two apart."""
    q = Question(
        id="version",
        prompt="Which version?",
        type="text",
        choices=None,
        csv_columns=["Which version?"],
    )
    assert q.choices is None


def test_question_is_frozen():
    """Question is immutable; the loader derives new ones with replace()."""
    q = Question(id="x", prompt="x", type="single", choices=[], csv_columns=[])
    with pytest.raises(Exception):  # FrozenInstanceError
        q.id = "y"


def test_survey_flat_questions():
    """Survey.questions flattens groups in document order; the loader
    iterates it the way it iterated the old flat schema."""
    q1 = Question(id="a", prompt="A", type="single", choices=["x"], csv_columns=["A"])
    q2 = Question(id="b", prompt="B", type="text", choices=None, csv_columns=["B"])
    s = _survey([q1, q2])
    assert s.title == "t"
    assert [q.id for q in s.questions] == ["a", "b"]


from nixos_survey_lib.types import Bin, CrossTab


def test_bin_construction():
    b = Bin(label="Linux", count=14, percent=70.0, total=20)
    assert b.label == "Linux"
    assert b.count == 14
    assert b.percent == 70.0
    assert b.total == 20


def test_crosstab_construction():
    ct = CrossTab(
        x_labels=["Beginner", "Advanced"],
        y_labels=["<2 years", "5+ years"],
        cells=[[10.0, 0.0], [2.0, 8.0]],
        cell_kind="rate_pct",
    )
    assert ct.cell_kind == "rate_pct"
    assert ct.cells[1][1] == 8.0


from nixos_survey_lib.types import ChartSpec, Page, Row, Section


def test_chartspec_optional_height():
    c = ChartSpec(option={"series": []})
    assert c.height is None
    c2 = ChartSpec(option={"series": []}, height=240)
    assert c2.height == 240


def test_row_construction():
    r = Row(
        id="country",
        title="Country",
        question="Where?",
        commentary="X.",
        charts=[ChartSpec(option={})],
    )
    assert r.id == "country"
    assert len(r.charts) == 1


def test_section_construction():
    r = Row(
        id="country",
        title="Country",
        question="Where?",
        commentary="X.",
        charts=[ChartSpec(option={})],
    )
    s = Section(id="people", heading="People", rows=[r])
    assert len(s.rows) == 1


def test_page_default_schema_version():
    p = Page(year=2025, title="Test", sections=[])
    assert p.schema_version == 1


import polars as pl
from nixos_survey_lib.types import MultiChoice, Ranking, SingleChoice, TextResponse


def _q(qid: str, qtype: str = "single") -> Question:
    return Question(id=qid, prompt=qid, type=qtype, choices=None, csv_columns=[])


def test_single_choice_len():
    s = SingleChoice(question=_q("a"), values=pl.Series(["x", "y", "z"]))
    assert len(s) == 3


def test_multi_choice_choices():
    m = MultiChoice(
        question=_q("a", "multiple"),
        choice_columns={"Linux": pl.Series(["Yes", "No"]), "macOS": pl.Series(["No", "Yes"])},
    )
    assert m.choices() == ["Linux", "macOS"]
    assert len(m) == 2


def test_ranking_len():
    r = Ranking(
        question=_q("a", "ranking"),
        rank_columns=[pl.Series(["A", "B"]), pl.Series(["B", "A"])],
    )
    assert len(r) == 2


def test_text_response_len():
    t = TextResponse(question=_q("a", "text"), values=pl.Series(["v1", "v2", "v3", "v4"]))
    assert len(t) == 4


from nixos_survey_lib.types import Responses


def test_responses_attribute_access():
    """Responses exposes each question as an attribute, r.country."""
    s = SingleChoice(question=_q("country"), values=pl.Series(["Europe", "Asia"]))
    r = Responses(schema=_survey([_q("country")]), by_id={"country": s})
    assert r.country is s


def test_responses_item_access():
    """Responses also supports item access, r["country"], for ids that are
    computed at runtime."""
    s = SingleChoice(question=_q("country"), values=pl.Series(["Europe"]))
    r = Responses(schema=_survey([_q("country")]), by_id={"country": s})
    assert r["country"] is s


def test_responses_unknown_id_raises():
    """An unknown id raises KeyError naming the id, not a bare KeyError."""
    r = Responses(schema=_survey([]), by_id={})
    with pytest.raises(KeyError) as exc:
        r["nope"]
    assert "nope" in str(exc.value)


def test_responses_iter_and_keys():
    """Iteration and keys() list the loaded question ids."""
    s = SingleChoice(question=_q("country"), values=pl.Series([]))
    r = Responses(schema=_survey([_q("country")]), by_id={"country": s})
    assert list(r) == ["country"]
    assert "country" in r.keys()
