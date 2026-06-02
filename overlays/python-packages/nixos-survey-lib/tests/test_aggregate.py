import polars as pl
import pytest

from nixos_survey_lib.aggregate import counts_single
from nixos_survey_lib.types import Bin, Question, SingleChoice


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
