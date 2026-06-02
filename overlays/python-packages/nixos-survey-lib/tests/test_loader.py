import textwrap

import pytest

from nixos_survey_lib.loader import load_schema


def _write_yaml(tmp_path, text):
    p = tmp_path / "s.yaml"
    p.write_text(textwrap.dedent(text))
    return p


def test_load_schema_returns_all_questions(fixtures_dir):
    schema = load_schema(fixtures_dir / "tiny_survey.yaml")
    assert schema.title == "Tiny Test Survey"
    assert len(schema.questions) == 6
    assert [q.id for q in schema.questions] == [
        "country", "os", "priorities", "nix_version", "skill", "long_prompt_question"
    ]


def test_load_schema_preserves_types_and_choices(fixtures_dir):
    schema = load_schema(fixtures_dir / "tiny_survey.yaml")
    by_id = {q.id: q for q in schema.questions}
    assert by_id["country"].type == "single"
    assert by_id["os"].type == "multiple"
    assert by_id["priorities"].type == "ranking"
    assert by_id["nix_version"].type == "text"
    assert by_id["country"].choices == [
        "Africa", "Asia", "Europe", "North America", "Prefer not to say"
    ]
    assert by_id["nix_version"].choices is None


def test_load_schema_rejects_missing_id(tmp_path):
    p = _write_yaml(tmp_path, """
        title: t
        questions:
          - prompt: hi
            type: single
            choices: [a]
    """)
    with pytest.raises(ValueError, match="missing 'id'"):
        load_schema(p)


def test_load_schema_rejects_non_identifier_id(tmp_path):
    p = _write_yaml(tmp_path, """
        title: t
        questions:
          - id: "1bad"
            prompt: hi
            type: single
            choices: [a]
    """)
    with pytest.raises(ValueError, match="not a valid Python identifier"):
        load_schema(p)


def test_load_schema_rejects_duplicate_ids(tmp_path):
    p = _write_yaml(tmp_path, """
        title: t
        questions:
          - id: dup
            prompt: a
            type: single
            choices: [x]
          - id: dup
            prompt: b
            type: single
            choices: [y]
    """)
    with pytest.raises(ValueError, match="duplicate question id"):
        load_schema(p)
