import csv

from nixos_survey_lib.loader import load_responses
from nixos_survey_lib.schema import load_survey
from nixos_survey_lib.synthesize import synthesize_csv


def _generate(fixtures_dir, tmp_path, **kwargs):
    schema = load_survey(fixtures_dir / "tiny_survey.toml")
    out = tmp_path / "synthetic.csv"
    synthesize_csv(schema, out, **kwargs)
    return schema, out


def test_synthesize_deterministic_for_fixed_seed(fixtures_dir, tmp_path):
    schema = load_survey(fixtures_dir / "tiny_survey.toml")
    a = tmp_path / "a.csv"
    b = tmp_path / "b.csv"
    synthesize_csv(schema, a, rows=50, seed=7)
    synthesize_csv(schema, b, rows=50, seed=7)
    assert a.read_bytes() == b.read_bytes()


def test_synthesize_differs_across_seeds(fixtures_dir, tmp_path):
    schema = load_survey(fixtures_dir / "tiny_survey.toml")
    a = tmp_path / "a.csv"
    b = tmp_path / "b.csv"
    synthesize_csv(schema, a, rows=50, seed=7)
    synthesize_csv(schema, b, rows=50, seed=8)
    assert a.read_bytes() != b.read_bytes()


def test_synthesize_row_count(fixtures_dir, tmp_path):
    _, out = _generate(fixtures_dir, tmp_path, rows=37, seed=1)
    with out.open(newline="") as f:
        n_rows = sum(1 for _ in csv.reader(f))
    assert n_rows == 38  # header + 37 data rows


def test_synthesize_round_trips_through_loader(fixtures_dir, tmp_path):
    # load_responses hard-fails on any missing column and enforces strict
    # survey-choice / CSV-column equality for multi-choice questions, so a
    # clean round-trip is the core structural guarantee.
    schema, out = _generate(fixtures_dir, tmp_path, rows=200, seed=3)
    r = load_responses(out, schema=schema)
    assert set(r.keys()) == {q.id for q in schema.questions}


def test_synthesize_single_values_within_choices(fixtures_dir, tmp_path):
    schema, out = _generate(fixtures_dir, tmp_path, rows=200, seed=3)
    r = load_responses(out, schema=schema)
    values = set(r["country"].values.to_list())
    allowed = {"Africa", "Asia", "Europe", "North America", "Prefer not to say", "Skipped"}
    assert values <= allowed


def test_synthesize_multi_columns_are_yes_no(fixtures_dir, tmp_path):
    _, out = _generate(fixtures_dir, tmp_path, rows=100, seed=2)
    cols = [
        "Which operating systems do you use? [Linux]",
        "Which operating systems do you use? [macOS]",
        "Which operating systems do you use? [Windows]",
    ]
    with out.open(newline="") as f:
        values = {row[c] for row in csv.DictReader(f) for c in cols}
    assert values <= {"Yes", "No"}


def test_synthesize_rankings_are_full_permutations_or_skipped(fixtures_dir, tmp_path):
    _, out = _generate(fixtures_dir, tmp_path, rows=200, seed=3)
    rank_cols = [
        "Rank your priorities. [Rank 1]",
        "Rank your priorities. [Rank 2]",
        "Rank your priorities. [Rank 3]",
    ]
    with out.open(newline="") as f:
        for row in csv.DictReader(f):
            ranks = [row[c] for c in rank_cols]
            if ranks == ["", "", ""]:
                continue
            assert sorted(ranks) == ["Documentation", "Performance", "Security"]


def test_synthesize_text_pool_respected(fixtures_dir, tmp_path):
    pool = ["2.18.1", "no idea"]
    schema, out = _generate(
        fixtures_dir, tmp_path, rows=100, seed=5, text_pools={"nixVersion": pool}
    )
    r = load_responses(out, schema=schema)
    values = set(r["nixVersion"].values.to_list())
    assert values <= {"2.18.1", "no idea", "Skipped"}
