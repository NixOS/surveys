import re
from pathlib import Path

import yaml

from .types import Question, SurveySchema

_WS_RUN = re.compile(r"\s+", re.UNICODE)
_BRACKET_SUFFIX = re.compile(r"^(.*)\s*\[([^\]]+)\]\s*$", re.DOTALL)


def strip_bracket_suffix(header: str) -> tuple[str, str | None]:
    """Split a CSV header into (base_prompt, bracket_contents). If no trailing
    [bracketed] suffix, returns (header, None)."""
    m = _BRACKET_SUFFIX.match(header)
    if not m:
        return header, None
    return m.group(1).rstrip(), m.group(2).strip()


def normalize_prompt(text: str) -> str:
    """Collapse all whitespace runs (newlines, tabs, NBSP) to single spaces
    and strip leading/trailing whitespace. Used to compare YAML prompts
    against CSV column headers."""
    return _WS_RUN.sub(" ", text.replace("\u00a0", " ")).strip()


def load_schema(yaml_path: Path) -> SurveySchema:
    """Parse a survey.yaml file into a typed SurveySchema with validation."""
    raw = yaml.safe_load(yaml_path.read_text())
    title = raw["title"]
    questions: list[Question] = []
    seen_ids: set[str] = set()
    for q in raw["questions"]:
        if "id" not in q:
            raise ValueError(f"question {q.get('prompt', '?')!r} is missing 'id'")
        qid = q["id"]
        if not qid.isidentifier():
            raise ValueError(
                f"question id {qid!r} is not a valid Python identifier"
            )
        if qid in seen_ids:
            raise ValueError(f"duplicate question id {qid!r}")
        seen_ids.add(qid)
        questions.append(
            Question(
                id=qid,
                prompt=q["prompt"],
                type=q["type"],
                choices=q.get("choices"),
                csv_columns=[],
            )
        )
    return SurveySchema(title=title, questions=questions)
