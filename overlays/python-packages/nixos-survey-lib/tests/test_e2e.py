import json

from nixos_survey_lib.aggregate import (
    counts_multi,
    counts_single,
)
from nixos_survey_lib.loader import load_responses, load_schema
from nixos_survey_lib.normalize import extract_first_semver
from nixos_survey_lib.page import page_to_json
from nixos_survey_lib.render_echarts import (
    horizontal_bar,
)
from nixos_survey_lib.types import Page, Row, Section


def test_e2e_pipeline_against_fixtures(fixtures_dir):
    """End-to-end: load fixture survey, build a Page, serialize, diff against golden."""
    schema = load_schema(fixtures_dir / "tiny_survey.yaml")
    r = load_responses(fixtures_dir / "tiny_responses.csv", schema=schema)

    nix_versions = extract_first_semver(r.nix_version)

    page = Page(
        year=2025,
        title="Tiny Survey Test",
        sections=[
            Section("demographics", "Demographics", rows=[
                Row("country", "Country",
                    question=r.country.question.prompt,
                    commentary="Europe leads in the synthetic fixture.",
                    charts=[horizontal_bar(
                        counts_single(r.country, bucket_min_percent=None, bucket_min_count=None))]),
                Row("skill", "Skill",
                    question=r.skill.question.prompt,
                    commentary="Distribution across three buckets.",
                    charts=[horizontal_bar(
                        counts_single(r.skill, bucket_min_percent=None, bucket_min_count=None,
                                       order=["Beginner", "Intermediate", "Advanced"]))]),
            ]),
            Section("tech", "Technology", rows=[
                Row("os", "Operating systems",
                    question=r.os.question.prompt,
                    commentary="Linux universal.",
                    charts=[horizontal_bar(counts_multi(r.os, bucket_min_percent=None, bucket_min_count=None))]),
                Row("nix_version", "Nix version",
                    question=r.nix_version.question.prompt,
                    commentary="Extracted from free-text.",
                    charts=[horizontal_bar(
                        counts_single(nix_versions, bucket_min_percent=None, bucket_min_count=None))]),
            ]),
            Section("ranking", "Ranking", rows=[
                Row("os2", "Operating systems (again)",
                    question=r.os.question.prompt,
                    commentary="Reuse os as a non-ranking placeholder.",
                    charts=[horizontal_bar(counts_multi(r.os, bucket_min_percent=None, bucket_min_count=None))]),
            ]),
        ],
    )

    actual = json.loads(page_to_json(page))
    expected = json.loads((fixtures_dir / "expected_results.json").read_text())
    assert actual == expected
