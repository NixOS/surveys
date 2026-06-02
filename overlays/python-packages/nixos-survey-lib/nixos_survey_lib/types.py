from dataclasses import dataclass
from typing import Literal


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
