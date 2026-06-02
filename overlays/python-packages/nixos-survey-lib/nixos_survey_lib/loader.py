import html
import re
from pathlib import Path

import polars as pl
import yaml

from .types import (
    MultiChoice,
    Question,
    Ranking,
    Responses,
    SingleChoice,
    SurveySchema,
    TextResponse,
)

_WS_RUN = re.compile(r"\s+", re.UNICODE)
_BRACKET_SUFFIX = re.compile(r"^(.*)\s*\[([^\]]+)\]\s*$", re.DOTALL)


def strip_bracket_suffix(header: str) -> tuple[str, str | None]:
    """Split a CSV header into (base_prompt, bracket_contents). If no trailing
    [bracketed] suffix, returns (header, None). HTML entities in the bracket
    content are decoded so values like ``|&gt;`` become ``|>``."""
    m = _BRACKET_SUFFIX.match(header)
    if not m:
        return header, None
    return m.group(1).rstrip(), html.unescape(m.group(2).strip())


def normalize_prompt(text: str) -> str:
    """Collapse all whitespace runs (newlines, tabs, NBSP) to single spaces,
    remove YAML list-item markers (``- ``), collapse CSV-escaped double-quotes
    (``""`` → ``"``), decode HTML entities, and strip leading/trailing whitespace.

    Used to compare YAML prompts against CSV column headers, which may differ
    due to survey-platform export artefacts:
    - CSV export doubles internal double-quotes (``""``).
    - CSV export HTML-entity-escapes characters like ``>`` (``&gt;``).
    - YAML block-scalar list prompts contain ``- `` list-item markers that the
      survey platform strips when building CSV column headers.
    """
    # Collapse whitespace first so YAML list markers become " - " uniformly.
    text = _WS_RUN.sub(" ", text.replace("\u00a0", " "))
    # Collapse doubled double-quotes produced by CSV export (e.g. ""uname -a"")
    text = text.replace('""', '"')
    # Decode HTML entities (e.g. &gt; → >, &amp; → &).
    text = html.unescape(text)
    # Remove YAML block-scalar list-item markers that don't appear in CSV headers.
    # Safe: no CSV base-prompt contains ` - ` (verified against this dataset).
    text = text.replace(" - ", " ")
    return _WS_RUN.sub(" ", text).strip()


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


def _clean_single_values(series: pl.Series) -> pl.Series:
    """Strip whitespace; empty/null -> 'Skipped'."""
    return (
        series.cast(pl.Utf8)
        .str.strip_chars()
        .replace("", None)
        .fill_null("Skipped")
    )


def load_responses(csv_path: Path, *, schema: SurveySchema) -> Responses:
    """Read the CSV and produce typed Responses by matching columns to schema
    questions via normalized prompt text."""
    df = pl.read_csv(csv_path)

    # Build a lookup from normalized header -> raw column name.
    normalized_headers: dict[str, str] = {}
    for col in df.columns:
        normalized_headers[normalize_prompt(col)] = col

    # Build a lookup from (normalized base prompt) -> list of (raw column, bracket content)
    # for headers that have a trailing [...] suffix.
    bracketed_headers: dict[str, list[tuple[str, str]]] = {}
    for col in df.columns:
        base, suffix = strip_bracket_suffix(col)
        if suffix is None:
            continue
        norm_base = normalize_prompt(base)
        bracketed_headers.setdefault(norm_base, []).append((col, suffix))

    by_id: dict[str, SingleChoice | MultiChoice | Ranking | TextResponse] = {}

    for q in schema.questions:
        norm_prompt = normalize_prompt(q.prompt)

        if q.type == "single":
            col = normalized_headers.get(norm_prompt)
            if col is None:
                raise ValueError(
                    f"no CSV column matches question id {q.id!r} (prompt: {q.prompt!r})"
                )
            updated = Question(
                id=q.id, prompt=q.prompt, type=q.type,
                choices=q.choices, csv_columns=[col],
            )
            by_id[q.id] = SingleChoice(question=updated, values=_clean_single_values(df[col]))

        elif q.type == "text":
            col = normalized_headers.get(norm_prompt)
            if col is None:
                raise ValueError(
                    f"no CSV column matches question id {q.id!r} (prompt: {q.prompt!r})"
                )
            updated = Question(
                id=q.id, prompt=q.prompt, type=q.type,
                choices=q.choices, csv_columns=[col],
            )
            cleaned = _clean_single_values(df[col])
            by_id[q.id] = TextResponse(question=updated, values=cleaned)

        elif q.type == "multiple":
            matches = bracketed_headers.get(norm_prompt, [])
            if not matches:
                raise ValueError(
                    f"no CSV columns matched question id {q.id!r} (prompt: {q.prompt!r})"
                )
            if q.choices is None:
                choice_order = [suffix for _, suffix in matches]
            else:
                by_suffix = {suffix: col for col, suffix in matches}
                choice_order = [c for c in q.choices if c in by_suffix]
            choice_columns_dict: dict[str, pl.Series] = {}
            cols: list[str] = []
            by_suffix_full = {suffix: col for col, suffix in matches}
            for c in choice_order:
                col = by_suffix_full[c]
                choice_columns_dict[c] = df[col]
                cols.append(col)
            updated = Question(
                id=q.id, prompt=q.prompt, type=q.type,
                choices=q.choices, csv_columns=cols,
            )
            by_id[q.id] = MultiChoice(question=updated, choice_columns=choice_columns_dict)

        elif q.type == "ranking":
            matches = bracketed_headers.get(norm_prompt, [])
            if not matches:
                raise ValueError(
                    f"no CSV columns matched question id {q.id!r} (prompt: {q.prompt!r})"
                )
            indexed: list[tuple[int, str]] = []
            for col, suffix in matches:
                m = re.match(r"^Rank\s+(\d+)$", suffix)
                if not m:
                    raise ValueError(
                        f"ranking column {col!r} has non-'Rank N' suffix {suffix!r}"
                    )
                indexed.append((int(m.group(1)), col))
            indexed.sort()
            rank_cols = [df[col] for _, col in indexed]
            rcols = [col for _, col in indexed]
            updated = Question(
                id=q.id, prompt=q.prompt, type=q.type,
                choices=q.choices, csv_columns=rcols,
            )
            by_id[q.id] = Ranking(question=updated, rank_columns=rank_cols)

    return Responses(schema=schema, by_id=by_id)


def load_commentary(path: Path) -> dict[str, str]:
    """Parse a flat markdown commentary file into {row_id: body}.

    Format: each row's commentary lives under a single `## <row-id>`
    second-level heading. Headings of other levels are preserved verbatim
    inside the body. Empty bodies (just the heading with no text) map to
    an empty string.
    """
    text = path.read_text()
    out: dict[str, str] = {}
    current_id: str | None = None
    current_body: list[str] = []

    def flush() -> None:
        nonlocal current_id, current_body
        if current_id is None:
            return
        body = "\n".join(current_body).strip("\n").strip()
        out[current_id] = body

    for line in text.splitlines():
        m = re.match(r"^##\s+([A-Za-z_][A-Za-z0-9_]*)\s*$", line)
        if m:
            flush()
            current_id = m.group(1)
            current_body = []
        else:
            if current_id is not None:
                current_body.append(line)

    flush()
    return out
