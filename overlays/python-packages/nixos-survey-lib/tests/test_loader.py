from nixos_survey_lib.loader import load_schema


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
