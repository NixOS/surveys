from pathlib import Path

import yaml

from .types import Question, SurveySchema


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
