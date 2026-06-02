from collections.abc import Iterator, KeysView
from dataclasses import dataclass
from typing import Any, Literal

import polars as pl


QuestionType = Literal["single", "multiple", "ranking", "text"]


@dataclass(frozen=True)
class Question:
    id: str
    prompt: str
    type: QuestionType
    choices: list[str] | None
    csv_columns: list[str]


@dataclass(frozen=True)
class SurveySchema:
    title: str
    questions: list[Question]


@dataclass(frozen=True)
class Bin:
    label: str
    count: int
    percent: float


@dataclass(frozen=True)
class CrossTab:
    x_labels: list[str]
    y_labels: list[str]
    cells: list[list[float]]
    cell_kind: Literal["count", "rate_pct", "composition_pct", "lift"]


@dataclass(frozen=True)
class Ranked:
    label: str
    value: float
    method: Literal["avg_rank", "top_n_count"]


@dataclass(frozen=True)
class ChartSpec:
    option: dict[str, Any]
    height: int | None = None


@dataclass(frozen=True)
class Row:
    id: str
    title: str
    commentary: str
    chart: ChartSpec


@dataclass(frozen=True)
class Section:
    id: str
    heading: str
    rows: list[Row]


@dataclass(frozen=True)
class Page:
    year: int
    title: str
    sections: list[Section]
    schema_version: int = 1


class SingleChoice:
    """One CSV column, one categorical value per respondent."""

    question: Question
    values: pl.Series

    def __init__(self, *, question: Question, values: pl.Series) -> None:
        self.question = question
        self.values = values

    def __len__(self) -> int:
        return len(self.values)


class MultiChoice:
    """N CSV columns, one per choice, each holding Yes/No/null."""

    question: Question
    choice_columns: dict[str, pl.Series]

    def __init__(self, *, question: Question, choice_columns: dict[str, pl.Series]) -> None:
        self.question = question
        self.choice_columns = choice_columns

    def __len__(self) -> int:
        if not self.choice_columns:
            return 0
        return len(next(iter(self.choice_columns.values())))

    def choices(self) -> list[str]:
        return list(self.choice_columns.keys())


class Ranking:
    """N CSV columns, one per rank position (1..N), each holding choice names."""

    question: Question
    rank_columns: list[pl.Series]

    def __init__(self, *, question: Question, rank_columns: list[pl.Series]) -> None:
        self.question = question
        self.rank_columns = rank_columns

    def __len__(self) -> int:
        return len(self.rank_columns[0]) if self.rank_columns else 0


class TextResponse:
    """One CSV column, free-text values."""

    question: Question
    values: pl.Series

    def __init__(self, *, question: Question, values: pl.Series) -> None:
        self.question = question
        self.values = values

    def __len__(self) -> int:
        return len(self.values)


ResponseUnion = SingleChoice | MultiChoice | Ranking | TextResponse


class Responses:
    """Container of typed responses indexed by question id.

    Both attribute access (r.country) and item access (r["country"]) work.
    Missing ids raise KeyError naming the available ids in the message.
    """

    schema: SurveySchema
    _by_id: dict[str, ResponseUnion]

    def __init__(self, *, schema: SurveySchema, by_id: dict[str, ResponseUnion]) -> None:
        self.schema = schema
        self._by_id = by_id

    def __getitem__(self, qid: str) -> ResponseUnion:
        if qid not in self._by_id:
            available = ", ".join(sorted(self._by_id)) or "(none)"
            raise KeyError(f"unknown question id {qid!r}; available: {available}")
        return self._by_id[qid]

    def __getattr__(self, qid: str) -> ResponseUnion:
        # __getattr__ is only called when normal attribute lookup fails. Use
        # object.__getattribute__ to read _by_id without re-triggering this
        # method, which would happen on the very first call before _by_id is
        # set during __init__.
        try:
            by_id: dict[str, ResponseUnion] = object.__getattribute__(self, "_by_id")
        except AttributeError:
            raise AttributeError(qid) from None
        if qid in by_id:
            return by_id[qid]
        raise AttributeError(f"no question id {qid!r}")

    def __iter__(self) -> Iterator[str]:
        return iter(self._by_id)

    def keys(self) -> KeysView[str]:
        return self._by_id.keys()
