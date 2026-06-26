import json
from pathlib import Path
from typing import Any

from .types import ChartSpec, Page, Row, Section


def page_to_json(page: Page, *, indent: int = 2) -> str:
    """Serialize a Page to a JSON string conforming to schema_version 1."""
    return json.dumps(_page_dict(page), indent=indent, sort_keys=False)


def write_page(page: Page, path: Path) -> None:
    """Write a Page to a JSON file."""
    path.write_text(page_to_json(page))


def _page_dict(page: Page) -> dict[str, Any]:
    return {
        "schema_version": page.schema_version,
        "series": page.series,
        "year": page.year,
        "title": page.title,
        "intro_meta": page.intro_meta,
        "intro_paragraphs": page.intro_paragraphs,
        "sections": [_section_dict(s) for s in page.sections],
    }


def _section_dict(s: Section) -> dict[str, Any]:
    return {
        "id": s.id,
        "heading": s.heading,
        "note": s.note,
        "rows": [_row_dict(r) for r in s.rows],
    }


def _row_dict(r: Row) -> dict[str, Any]:
    return {
        "id": r.id,
        "title": r.title,
        "question": r.question,
        "commentary": r.commentary,
        "charts": [_chart_dict(c) for c in r.charts],
        "wide": r.wide,
    }


def _chart_dict(c: ChartSpec) -> dict[str, Any]:
    out: dict[str, Any] = {"option": c.option}
    if c.height is not None:
        out["height"] = c.height
    if c.caption is not None:
        out["caption"] = c.caption
    if c.key is not None:
        out["key"] = c.key
    return out
