import json

from nixos_survey_lib.page import page_to_json, write_page
from nixos_survey_lib.types import ChartSpec, Page, Row, Section


def _sample_page() -> Page:
    return Page(
        year=2025,
        title="Test",
        sections=[
            Section(id="people", heading="People", rows=[
                Row(id="country", title="Country", question="Where?", commentary="Europe leads.",
                    chart=ChartSpec(option={"series": [{"type": "bar", "data": [1]}]}, height=240)),
            ]),
        ],
    )


def test_page_to_json_structure():
    p = _sample_page()
    out = json.loads(page_to_json(p))
    assert out["schema_version"] == 1
    assert out["year"] == 2025
    assert out["title"] == "Test"
    assert out["sections"][0]["id"] == "people"
    row = out["sections"][0]["rows"][0]
    assert row["id"] == "country"
    assert row["chart"]["option"]["series"][0]["data"] == [1]
    assert row["chart"]["height"] == 240


def test_page_to_json_omits_optional_height_when_none():
    p = Page(year=2026, title="t", sections=[
        Section(id="s", heading="S", rows=[
            Row(id="r", title="R", question="?", commentary="",
                chart=ChartSpec(option={}, height=None)),
        ]),
    ])
    out = json.loads(page_to_json(p))
    assert "height" not in out["sections"][0]["rows"][0]["chart"]


def test_write_page_writes_file(tmp_path):
    p = _sample_page()
    target = tmp_path / "results.json"
    write_page(p, target)
    out = json.loads(target.read_text())
    assert out["year"] == 2025
