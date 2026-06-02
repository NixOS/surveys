from dataclasses import dataclass
from typing import Literal

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
    option: dict
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

    def __init__(self, *, question: Question, values: pl.Series) -> None:
        self.question = question
        self.values = values

    def __len__(self) -> int:
        return len(self.values)


class MultiChoice:
    """N CSV columns, one per choice, each holding Yes/No/null."""

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

    def __init__(self, *, question: Question, rank_columns: list[pl.Series]) -> None:
        self.question = question
        self.rank_columns = rank_columns

    def __len__(self) -> int:
        return len(self.rank_columns[0]) if self.rank_columns else 0


class TextResponse:
    """One CSV column, free-text values."""

    def __init__(self, *, question: Question, values: pl.Series) -> None:
        self.question = question
        self.values = values

    def __len__(self) -> int:
        return len(self.values)
