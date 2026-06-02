import polars as pl
import pytest

from nixos_survey_lib.aggregate import counts_multi, counts_single, crosstab, crosstab_multi, ranking_avg, ranking_top_n
from nixos_survey_lib.types import Bin, MultiChoice, Question, Ranked, Ranking, SingleChoice


def _sc(values: list[str], qid: str = "country") -> SingleChoice:
    q = Question(id=qid, prompt=qid, type="single", choices=None, csv_columns=[])
    return SingleChoice(question=q, values=pl.Series(values))


def test_counts_single_basic():
    s = _sc(["Europe", "Europe", "Asia", "Europe"])
    bins = counts_single(s, bucket_min_percent=None)
    by_label = {b.label: b for b in bins}
    assert by_label["Europe"].count == 3
    assert by_label["Europe"].percent == 75.0
    assert by_label["Asia"].count == 1
    assert by_label["Asia"].percent == 25.0


def test_counts_single_respects_order():
    s = _sc(["Asia", "Europe", "Asia", "Europe"])
    bins = counts_single(s, order=["Europe", "Asia"], bucket_min_percent=None)
    assert [b.label for b in bins] == ["Europe", "Asia"]


def test_counts_single_exclude():
    s = _sc(["Europe", "Skipped", "Asia", "Skipped"])
    bins = counts_single(s, exclude=["Skipped"], bucket_min_percent=None)
    labels = {b.label for b in bins}
    assert "Skipped" not in labels
    by_label = {b.label: b for b in bins}
    assert by_label["Europe"].percent == 50.0


def test_counts_single_bucket_min_percent():
    s = _sc(["A"] * 95 + ["B"] * 3 + ["C"] * 2)
    bins = counts_single(s, bucket_min_percent=5.0)
    by_label = {b.label: b for b in bins}
    assert "A" in by_label
    assert "Other" in by_label
    assert by_label["Other"].count == 5


def test_counts_single_empty():
    s = _sc([])
    bins = counts_single(s)
    assert bins == []


def _mc(choice_columns: dict[str, list[str]]) -> MultiChoice:
    q = Question(id="x", prompt="x", type="multiple", choices=list(choice_columns), csv_columns=[])
    return MultiChoice(question=q, choice_columns={k: pl.Series(v) for k, v in choice_columns.items()})


def test_counts_multi_basic():
    m = _mc({
        "Linux": ["Yes", "Yes", "Yes", "Yes"],
        "macOS": ["No", "Yes", "Yes", "No"],
        "Windows": ["No", "No", "No", "Yes"],
    })
    bins = counts_multi(m, bucket_min_percent=None)
    by_label = {b.label: b for b in bins}
    assert by_label["Linux"].count == 4
    assert by_label["Linux"].percent == 100.0
    assert by_label["macOS"].count == 2
    assert by_label["macOS"].percent == 50.0
    assert by_label["Windows"].count == 1
    assert by_label["Windows"].percent == 25.0


def test_counts_multi_sorted_by_percent_desc():
    m = _mc({
        "A": ["No", "Yes"],
        "B": ["Yes", "Yes"],
        "C": ["No", "No"],
    })
    bins = counts_multi(m, bucket_min_percent=None)
    assert [b.label for b in bins] == ["B", "A", "C"]


def test_counts_multi_bucket_min_percent():
    m = _mc({
        "A": ["Yes"] * 100,
        "B": ["Yes"] * 1 + ["No"] * 99,
        "C": ["Yes"] * 1 + ["No"] * 99,
    })
    bins = counts_multi(m, bucket_min_percent=5.0)
    labels = {b.label for b in bins}
    assert "A" in labels
    assert "Other" in labels
    assert "B" not in labels and "C" not in labels


def test_crosstab_global_normalize():
    x = _sc(["A", "A", "B", "B"], qid="x")
    y = _sc(["P", "Q", "P", "Q"], qid="y")
    ct = crosstab(x, y, normalize="global", x_order=["A", "B"], y_order=["P", "Q"])
    assert ct.cell_kind == "rate_pct"
    assert ct.cells == [[25.0, 25.0], [25.0, 25.0]]


def test_crosstab_x_normalize():
    x = _sc(["A", "A", "A", "B", "B"], qid="x")
    y = _sc(["P", "P", "Q", "P", "Q"], qid="y")
    ct = crosstab(x, y, normalize="x", x_order=["A", "B"], y_order=["P", "Q"])
    assert ct.cells[0][0] == pytest.approx(2 / 3 * 100, abs=0.01)
    assert ct.cells[0][1] == pytest.approx(1 / 3 * 100, abs=0.01)


def test_crosstab_y_normalize():
    x = _sc(["A", "A", "B"], qid="x")
    y = _sc(["P", "Q", "P"], qid="y")
    ct = crosstab(x, y, normalize="y", x_order=["A", "B"], y_order=["P", "Q"])
    assert ct.cells[0][0] == pytest.approx(50.0)
    assert ct.cells[1][0] == pytest.approx(50.0)


def test_crosstab_excludes_values():
    x = _sc(["A", "B", "Skipped"], qid="x")
    y = _sc(["P", "Q", "P"], qid="y")
    ct = crosstab(x, y, normalize="global", x_exclude=["Skipped"],
                  x_order=["A", "B"], y_order=["P", "Q"])
    assert "Skipped" not in ct.x_labels


def test_crosstab_empty_returns_empty():
    x = _sc([], qid="x")
    y = _sc([], qid="y")
    ct = crosstab(x, y)
    assert ct.x_labels == []
    assert ct.y_labels == []
    assert ct.cells == []


def _mc_long() -> tuple[MultiChoice, SingleChoice]:
    m = _mc({
        "trait_A": ["Yes", "Yes", "No", "No"],
        "trait_B": ["Yes", "No", "Yes", "No"],
    })
    s = _sc(["Beginner", "Advanced", "Beginner", "Advanced"], qid="skill")
    return m, s


def test_crosstab_multi_rate():
    m, s = _mc_long()
    ct = crosstab_multi(m, s, denominator="rate", x_order=["Beginner", "Advanced"])
    assert ct.cell_kind == "rate_pct"
    # cells[xi][yi]: xi indexes x_labels (single values), yi indexes y_labels (traits)
    by_label = {(t, x): ct.cells[j][i] for i, t in enumerate(ct.y_labels) for j, x in enumerate(ct.x_labels)}
    assert by_label[("trait_A", "Beginner")] == pytest.approx(50.0)
    assert by_label[("trait_A", "Advanced")] == pytest.approx(50.0)


def test_crosstab_multi_composition():
    m, s = _mc_long()
    ct = crosstab_multi(m, s, denominator="composition", x_order=["Beginner", "Advanced"])
    assert ct.cell_kind == "composition_pct"
    # cells[xi][yi]: xi indexes x_labels (single values), yi indexes y_labels (traits)
    by_label = {(t, x): ct.cells[j][i] for i, t in enumerate(ct.y_labels) for j, x in enumerate(ct.x_labels)}
    assert by_label[("trait_A", "Beginner")] == pytest.approx(50.0)
    assert by_label[("trait_A", "Advanced")] == pytest.approx(50.0)


def test_crosstab_multi_lift():
    m, s = _mc_long()
    ct = crosstab_multi(m, s, denominator="lift", x_order=["Beginner", "Advanced"])
    assert ct.cell_kind == "lift"
    # cells[xi][yi]: xi indexes x_labels (single values), yi indexes y_labels (traits)
    by_label = {(t, x): ct.cells[j][i] for i, t in enumerate(ct.y_labels) for j, x in enumerate(ct.x_labels)}
    assert by_label[("trait_A", "Beginner")] == pytest.approx(1.0)


def _rk(rows: list[list[str | None]]) -> Ranking:
    n_positions = len(rows[0]) if rows else 0
    cols = [[r[i] for r in rows] for i in range(n_positions)]
    q = Question(id="x", prompt="x", type="ranking", choices=None, csv_columns=[])
    return Ranking(question=q, rank_columns=[pl.Series(c) for c in cols])


def test_ranking_avg_sorts_ascending():
    r = _rk([
        ["A", "B", "C"],
        ["B", "A", "C"],
    ])
    out = ranking_avg(r)
    assert all(o.method == "avg_rank" for o in out)
    by = {o.label: o.value for o in out}
    assert by["A"] == pytest.approx(1.5)
    assert by["B"] == pytest.approx(1.5)
    assert by["C"] == pytest.approx(3.0)
    assert out[0].value <= out[-1].value


def test_ranking_avg_ignores_empty():
    r = _rk([
        ["A", "B", None],
        ["A", None, "B"],
    ])
    out = ranking_avg(r)
    by = {o.label: o.value for o in out}
    assert by["A"] == pytest.approx(1.0)
    assert by["B"] == pytest.approx(2.5)


def test_ranking_top_n_counts_appearances():
    r = _rk([
        ["A", "B", "C"],
        ["A", "C", "B"],
        ["B", "A", "C"],
        ["C", "A", "B"],
    ])
    out = ranking_top_n(r, n=2)
    by = {o.label: o.value for o in out}
    assert by["A"] == 4
    assert by["B"] == 2
    assert by["C"] == 2
    assert all(o.method == "top_n_count" for o in out)
    assert out[0].value >= out[-1].value
