import polars as pl
import pytest

from nixos_survey_lib.aggregate import counts_multi, counts_single
from nixos_survey_lib.types import Bin, MultiChoice, Question, SingleChoice


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
