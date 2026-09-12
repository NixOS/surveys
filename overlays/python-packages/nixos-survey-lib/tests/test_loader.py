"""Tests for nixos_survey_lib.loader: matching CSV columns to survey questions.

The survey definition comes from load_survey (TOML); the CSV is LimeSurvey's
response export with full-question-text headers. Rules about the TOML files
themselves live in test_schema.py.
"""

import textwrap

import pytest
from nixos_survey_lib.loader import (
    load_commentary,
    load_responses,
    normalize_prompt,
    strip_bracket_suffix,
)
from nixos_survey_lib.schema import load_survey


def _write_survey(tmp_path, structure: str, texts: str):
    """Write a structure file and its English text file, both dedented, and
    return the structure path for load_survey."""
    (tmp_path / "s.toml").write_text(textwrap.dedent(structure), encoding="utf-8")
    (tmp_path / "s.en.toml").write_text(textwrap.dedent(texts), encoding="utf-8")
    return tmp_path / "s.toml"


# Shared prefixes for one-question surveys; tests append a question each.
_HEADER = """
    [survey]
    id = 7
    language = "en"
    languages = ["en"]

    [survey.privacy]
    anonymized = true
    save_ip_address = false
    save_referrer = false
    date_stamp = false
    save_timings = false

    [[groups]]
    id = "g"
"""

_TEXT_HEADER = """
    [survey]
    title = "t"
    intro = "i"

    [groups.g]
    title = "G"
"""


def test_load_survey_returns_all_questions(fixtures_dir):
    """The fixture survey loads with its six questions in document order."""
    schema = load_survey(fixtures_dir / "tiny_survey.toml")
    assert schema.title == "Tiny Test Survey"
    assert len(schema.questions) == 6
    assert [q.id for q in schema.questions] == [
        "country",
        "os",
        "priorities",
        "nixVersion",
        "skill",
        "longPrompt",
    ]


def test_load_survey_preserves_types_and_choices(fixtures_dir):
    """Types and resolved English choice texts come through as the loader's
    column matching expects them: text questions have ``choices is None``."""
    schema = load_survey(fixtures_dir / "tiny_survey.toml")
    by_id = {q.id: q for q in schema.questions}
    assert by_id["country"].type == "single"
    assert by_id["os"].type == "multiple"
    assert by_id["priorities"].type == "ranking"
    assert by_id["nixVersion"].type == "text"
    assert by_id["country"].choices == [
        "Africa",
        "Asia",
        "Europe",
        "North America",
        "Prefer not to say",
    ]
    assert by_id["nixVersion"].choices is None


def test_normalize_prompt_collapses_whitespace():
    """Runs of whitespace -- spaces, tabs, newlines, CRLF -- collapse to a
    single space, and the result is stripped of leading and trailing
    whitespace."""
    assert normalize_prompt("  hello   world ") == "hello world"
    assert normalize_prompt("a\nb\tc") == "a b c"
    assert normalize_prompt("a\r\nb") == "a b"


def test_normalize_prompt_handles_nbsp():
    """A non-breaking space between words is treated like an ordinary space
    and collapses the same way."""
    assert normalize_prompt("a b") == "a b"


def test_normalize_prompt_idempotent():
    """Normalizing an already-normalized string is a no-op, so comparing two
    independently normalized prompts is safe."""
    assert normalize_prompt(normalize_prompt("  a  b  ")) == "a b"


def test_strip_bracket_suffix_choice():
    """A trailing ``[Choice]`` suffix on a multi-choice CSV header splits
    into the base prompt and the choice text."""
    base, suffix = strip_bracket_suffix("Which OS? [GNU/Linux]")
    assert base == "Which OS?"
    assert suffix == "GNU/Linux"


def test_strip_bracket_suffix_rank():
    """A ranking question's ``[Rank N]`` suffix splits off the same way as a
    choice suffix; the ``Rank N`` text itself comes back unparsed."""
    base, suffix = strip_bracket_suffix("Rank priorities. [Rank 3]")
    assert base == "Rank priorities."
    assert suffix == "Rank 3"


def test_strip_bracket_suffix_no_suffix():
    """A header with no trailing bracket is returned unchanged, with the
    suffix ``None``."""
    base, suffix = strip_bracket_suffix("Where do you live?")
    assert base == "Where do you live?"
    assert suffix is None


def test_strip_bracket_suffix_only_strips_trailing():
    """Only the final bracketed group is treated as the suffix; an earlier
    ``[bracketed]`` phrase inside the prompt text stays in the base
    prompt."""
    base, suffix = strip_bracket_suffix("Some [topic] question. [answer]")
    assert base == "Some [topic] question."
    assert suffix == "answer"


def test_load_responses_single_choice(fixtures_dir):
    """The `country` single-choice column is matched to its CSV column by
    prompt text; all 20 rows load in order and stay tied to their
    question."""
    schema = load_survey(fixtures_dir / "tiny_survey.toml")
    r = load_responses(fixtures_dir / "tiny_responses.csv", schema=schema)
    country = r.country
    assert len(country) == 20
    assert country.values[0] == "Europe"
    assert country.question.id == "country"


def test_load_responses_text(fixtures_dir):
    """The `nixVersion` text column loads all 20 rows; an empty CSV cell
    (row 15) is normalized to the literal string ``"Skipped"`` rather than
    an empty string or null."""
    schema = load_survey(fixtures_dir / "tiny_survey.toml")
    r = load_responses(fixtures_dir / "tiny_responses.csv", schema=schema)
    v = r.nixVersion
    assert len(v) == 20
    # Empty cell at row 15 (index 14) is normalized to "Skipped"
    assert v.values[14] == "Skipped"


def test_load_responses_handles_trailing_whitespace_in_header(fixtures_dir):
    """The CSV header for `country` carries a trailing space the survey
    platform's export adds (``"Where do you live? "``); the column still
    matches its question despite the extra whitespace."""
    schema = load_survey(fixtures_dir / "tiny_survey.toml")
    r = load_responses(fixtures_dir / "tiny_responses.csv", schema=schema)
    assert "country" in r.keys()


def test_load_responses_handles_multiline_prompt(fixtures_dir):
    """`longPrompt`'s TOML prompt spans multiple lines, but the CSV export
    collapses it onto one line; normalize_prompt reconciles the two so the
    column is still found."""
    schema = load_survey(fixtures_dir / "tiny_survey.toml")
    r = load_responses(fixtures_dir / "tiny_responses.csv", schema=schema)
    assert "longPrompt" in r.keys()
    assert len(r.longPrompt) == 20


def test_load_responses_multi_choice(fixtures_dir):
    """The `os` multi-choice question's bracketed CSV columns are matched by
    choice text and returned in the survey's declared choice order, with
    each choice's Yes/No values reachable by that same choice text."""
    schema = load_survey(fixtures_dir / "tiny_survey.toml")
    r = load_responses(fixtures_dir / "tiny_responses.csv", schema=schema)
    os = r.os
    assert os.choices() == ["Linux", "macOS", "Windows"]
    assert len(os) == 20
    assert os.choice_columns["Linux"][0] == "Yes"
    assert os.choice_columns["macOS"][0] == "No"


def test_load_responses_ranking(fixtures_dir):
    """The `priorities` ranking question collects its three ``[Rank N]``
    columns, and the first-ranked column's first value is the expected
    choice text. Unlike single/text columns, rank columns are not
    normalized: an unranked cell (row 18) comes through as ``""`` or
    ``None`` rather than being filled with ``"Skipped"``."""
    schema = load_survey(fixtures_dir / "tiny_survey.toml")
    r = load_responses(fixtures_dir / "tiny_responses.csv", schema=schema)
    pri = r.priorities
    assert len(pri.rank_columns) == 3
    assert len(pri) == 20
    assert pri.rank_columns[0][0] == "Performance"
    val = pri.rank_columns[0][17]
    assert val == "" or val is None


def test_load_responses_ranking_orders_by_rank_position(fixtures_dir):
    """Only checks that three rank columns are found; the fixture's CSV
    already lists ``[Rank 1]``/``[Rank 2]``/``[Rank 3]`` in that column
    order, so this alone does not exercise the sort-by-rank-number step."""
    schema = load_survey(fixtures_dir / "tiny_survey.toml")
    r = load_responses(fixtures_dir / "tiny_responses.csv", schema=schema)
    pri = r.priorities
    assert len(pri.rank_columns) == 3


def test_load_responses_errors_on_missing_csv_column(tmp_path, fixtures_dir):
    """If the CSV has none of the columns a schema question expects,
    load_responses raises ValueError naming the missing match instead of
    silently producing an empty result."""
    csv = tmp_path / "responses.csv"
    csv.write_text('"Some other column"\n"value"\n')
    schema = load_survey(fixtures_dir / "tiny_survey.toml")
    with pytest.raises(ValueError, match="no CSV column matches"):
        load_responses(csv, schema=schema)


def test_load_commentary_keyed_by_row_id(fixtures_dir):
    """load_commentary keys its result by the row id in each ``## <id>``
    heading, with the body text under a heading as that entry's value."""
    cm = load_commentary(fixtures_dir / "tiny_commentary.md")
    assert set(cm.keys()) == {"country", "skill", "os"}
    assert "Europe leads" in cm["country"]


def test_load_commentary_preserves_multiline(fixtures_dir):
    """A commentary body spanning multiple lines keeps its internal
    newlines rather than being joined onto one line."""
    cm = load_commentary(fixtures_dir / "tiny_commentary.md")
    assert "Multiline content\nis preserved." in cm["skill"]


def test_load_commentary_strips_trailing_blank_lines(fixtures_dir):
    """Trailing blank lines at the end of a commentary section are stripped
    from the body."""
    cm = load_commentary(fixtures_dir / "tiny_commentary.md")
    assert not cm["country"].endswith("\n\n")


def test_load_responses_errors_when_csv_has_extra_multi_choices(tmp_path):
    """If the CSV has multi-choice columns whose bracket suffix is not in
    the survey's choices, the loader must raise (silent drops hide real
    data-loss bugs)."""
    p = _write_survey(
        tmp_path,
        _HEADER
        + """
        [[groups.questions]]
        id = "os"
        type = "multiple"
        choices = ["linux", "macos"]
    """,
        _TEXT_HEADER
        + """
        [questions.os]
        prompt = "Which OS do you use?"
        choices.linux = "Linux"
        choices.macos = "macOS"
    """,
    )
    csv_p = tmp_path / "responses.csv"
    csv_p.write_text(
        '"Which OS do you use? [Linux]","Which OS do you use? [macOS]","Which OS do you use? [Windows]"\n'
        '"Yes","No","Yes"\n'
    )
    with pytest.raises(ValueError) as exc:
        load_responses(csv_p, schema=load_survey(p))
    msg = str(exc.value)
    assert "choice mismatch" in msg
    assert "'Windows'" in msg
    assert "CSV has 1 column" in msg


def test_load_responses_errors_when_survey_has_extra_multi_choices(tmp_path):
    """If the survey lists choices that have no matching CSV column, the
    loader must raise."""
    p = _write_survey(
        tmp_path,
        _HEADER
        + """
        [[groups.questions]]
        id = "os"
        type = "multiple"
        choices = ["linux", "macos", "windows", "bsd"]
    """,
        _TEXT_HEADER
        + """
        [questions.os]
        prompt = "Which OS do you use?"
        choices.linux = "Linux"
        choices.macos = "macOS"
        choices.windows = "Windows"
        choices.bsd = "BSD"
    """,
    )
    csv_p = tmp_path / "responses.csv"
    csv_p.write_text('"Which OS do you use? [Linux]","Which OS do you use? [macOS]"\n"Yes","No"\n')
    with pytest.raises(ValueError) as exc:
        load_responses(csv_p, schema=load_survey(p))
    msg = str(exc.value)
    assert "choice mismatch" in msg
    assert "'BSD'" in msg
    assert "'Windows'" in msg
    assert "survey has 2 choice" in msg
