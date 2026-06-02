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
