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


from nixos_survey_lib.types import Bin, CrossTab, Ranked


def test_bin_construction():
    b = Bin(label="Linux", count=14, percent=70.0)
    assert b.label == "Linux"
    assert b.count == 14
    assert b.percent == 70.0


def test_crosstab_construction():
    ct = CrossTab(
        x_labels=["Beginner", "Advanced"],
        y_labels=["<2 years", "5+ years"],
        cells=[[10.0, 0.0], [2.0, 8.0]],
        cell_kind="rate_pct",
    )
    assert ct.cell_kind == "rate_pct"
    assert ct.cells[1][1] == 8.0


def test_ranked_construction():
    r = Ranked(label="Documentation", value=2.28, method="avg_rank")
    assert r.label == "Documentation"
    assert r.method == "avg_rank"


from nixos_survey_lib.types import ChartSpec, Row, Section, Page


def test_chartspec_optional_height():
    c = ChartSpec(option={"series": []})
    assert c.height is None
    c2 = ChartSpec(option={"series": []}, height=240)
    assert c2.height == 240


def test_row_construction():
    r = Row(id="country", title="Country", question="Where?", commentary="X.", charts=[ChartSpec(option={})])
    assert r.id == "country"
    assert len(r.charts) == 1


def test_section_construction():
    r = Row(id="country", title="Country", question="Where?", commentary="X.", charts=[ChartSpec(option={})])
    s = Section(id="people", heading="People", rows=[r])
    assert len(s.rows) == 1


def test_page_default_schema_version():
    p = Page(year=2025, title="Test", sections=[])
    assert p.schema_version == 1


import polars as pl

from nixos_survey_lib.types import SingleChoice, MultiChoice, Ranking, TextResponse


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
    s = SingleChoice(question=_q("country"), values=pl.Series(["Europe", "Asia"]))
    schema = SurveySchema(title="t", questions=[_q("country")])
    r = Responses(schema=schema, by_id={"country": s})
    assert r.country is s


def test_responses_item_access():
    s = SingleChoice(question=_q("country"), values=pl.Series(["Europe"]))
    schema = SurveySchema(title="t", questions=[_q("country")])
    r = Responses(schema=schema, by_id={"country": s})
    assert r["country"] is s


def test_responses_unknown_id_raises():
    schema = SurveySchema(title="t", questions=[])
    r = Responses(schema=schema, by_id={})
    with pytest.raises(KeyError) as exc:
        r["nope"]
    assert "nope" in str(exc.value)


def test_responses_iter_and_keys():
    s = SingleChoice(question=_q("country"), values=pl.Series([]))
    schema = SurveySchema(title="t", questions=[_q("country")])
    r = Responses(schema=schema, by_id={"country": s})
    assert list(r) == ["country"]
    assert "country" in r.keys()
