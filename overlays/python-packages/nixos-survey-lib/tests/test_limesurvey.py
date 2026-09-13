"""Tests for nixos_survey_lib.limesurvey, the TSV survey-structure emitter.

The golden test pins the exact bytes for a small two-language survey; the
focused tests each cover one rule of the output format so a
regression names the rule rather than just "golden differs".
"""

import csv
import io
from pathlib import Path

import pytest
from nixos_survey_lib.limesurvey import COLUMNS, _row, html_text, plain, to_tsv, type_letter
from nixos_survey_lib.schema import Question, load_survey


def _rows(tsv: str) -> list[dict[str, str]]:
    """Parse emitter output back into one dict per row, keyed by column.

    Uses the csv module with the same delimiter and quote character the
    importer's fgetcsv uses, so quoted cells round-trip the same way.
    """
    assert tsv.startswith("\ufeff")
    reader = csv.reader(io.StringIO(tsv[1:]), delimiter="\t", quotechar='"')
    header = next(reader)
    assert header == list(COLUMNS)
    return [dict(zip(header, row)) for row in reader]


@pytest.fixture
def fixture_survey(fixtures_dir: Path):
    """The two-language golden fixture under tests/fixtures/limesurvey."""
    return load_survey(fixtures_dir / "limesurvey" / "survey.toml")


def test_golden_file(fixtures_dir, fixture_survey):
    """The emitter reproduces expected_survey.txt byte for byte. That file
    is written by make_expected.py beside it from an explicit row list, not
    from the emitter, so it is an independent oracle."""
    expected = (fixtures_dir / "limesurvey" / "expected_survey.txt").read_text(encoding="utf-8")
    assert to_tsv(fixture_survey) == expected


def test_output_starts_with_bom(fixture_survey):
    """The file starts with U+FEFF so it carries a UTF-8 byte-order mark,
    as LimeSurvey's own export does; the importer strips it."""
    tsv = to_tsv(fixture_survey)
    assert tsv[0] == "\ufeff" and tsv[1:3] == "id"
    assert tsv.encode("utf-8")[:3] == b"\xef\xbb\xbf"


def test_header_is_limesurveys_columns_plus_our_attributes():
    """The header is LimeSurvey's sixteen fixed columns, in its order, plus
    the two attribute columns we use. The importer reads every non-empty cell
    whose column is not in its skip list (class, type/scale, name, text,
    validation, relevance, help, language, mandatory, other, same_default,
    same_script, default) as a question attribute. That includes id,
    related_id and encrypted, which is why those cells stay empty."""
    assert len(COLUMNS) == 18
    assert COLUMNS[:16] == (
        "id",
        "related_id",
        "class",
        "type/scale",
        "name",
        "relevance",
        "text",
        "help",
        "language",
        "validation",
        "mandatory",
        "encrypted",
        "other",
        "default",
        "same_default",
        "same_script",
    )
    assert COLUMNS[16] == "max_answers"
    assert COLUMNS[17] == "answer_order"


def test_answer_order_on_reference_row_only(fixture_survey):
    """alphasort in the TOML becomes LimeSurvey's answer_order attribute,
    which supersedes the legacy alphasort one and is what the admin UI writes.
    Like max_answers it is language-independent, so only the reference row
    carries it."""
    rows = [
        r for r in _rows(to_tsv(fixture_survey)) if r["class"] == "Q" and r["name"] == "country"
    ]
    by_lang = {r["language"]: r["answer_order"] for r in rows}
    assert by_lang == {"en": "alphabetical", "de": ""}


def test_row_rejects_unknown_column():
    """A keyword that is not a column name is a typo, not a new attribute:
    the row builder would drop it silently, so it asserts instead."""
    with pytest.raises(AssertionError, match="mandatry"):
        _row(cls="Q", mandatry="N")


@pytest.mark.parametrize(
    "kwargs, letter",
    [
        pytest.param(dict(type="single"), "L", id="single-radio"),
        pytest.param(dict(type="single", display="dropdown"), "!", id="single-dropdown"),
        pytest.param(dict(type="multiple"), "M", id="multiple"),
        pytest.param(dict(type="ranking"), "R", id="ranking"),
        pytest.param(dict(type="text"), "T", id="text-long"),
        pytest.param(dict(type="text", size="short"), "S", id="text-short"),
    ],
)
def test_type_letter(kwargs, letter):
    """Each TOML type (plus display or size) maps to one LimeSurvey type
    letter."""
    q = Question(id="q", prompt="p", choices=None, **kwargs)
    assert type_letter(q) == letter


def test_mandatory_letters(fixture_survey):
    """off, soft, on become N, S, Y in the mandatory column."""
    rows = {
        r["name"]: r
        for r in _rows(to_tsv(fixture_survey))
        if r["class"] == "Q" and r["language"] == "en"
    }
    assert rows["country"]["mandatory"] == "N"
    assert rows["os"]["mandatory"] == "S"
    assert rows["age"]["mandatory"] == "Y"


def test_plain_collapses_whitespace_and_escapes():
    """Plain-text cells are single-line with & < > escaped; quotes are left
    alone because the csv layer handles them."""
    assert plain("  Nix  &\tNixOS\r\n <tools> ") == "Nix &amp; NixOS &lt;tools&gt;"
    assert plain('say "hi"') == 'say "hi"'


def test_html_text_collapses_newlines_only():
    """HTML cells (intro, end) pass through unescaped; only newlines are
    collapsed so the cell stays on one line."""
    assert html_text("<p>a</p>\r\n\n<p>b & c</p>") == "<p>a</p> <p>b & c</p>"


def test_sid_and_settings_rows(fixture_survey):
    """The S rows carry exactly the settings we own: survey id, languages,
    page format, and the five privacy flags as Y/N."""
    s = {r["name"]: r["text"] for r in _rows(to_tsv(fixture_survey)) if r["class"] == "S"}
    assert s == {
        "sid": "424242",
        "language": "en",
        "additional_languages": "de",
        "format": "G",
        "anonymized": "Y",
        "ipaddr": "N",
        "refurl": "N",
        "datestamp": "N",
        "savetimings": "N",
    }


def test_language_block_order(fixture_survey):
    """Row order matches LimeSurvey's exporter: all S rows, then all SL
    rows, then the whole G/Q/SQ/A block once per language, reference
    language first. The importer links translations by position within
    these blocks."""
    rows = _rows(to_tsv(fixture_survey))
    classes = [r["class"] for r in rows]
    first_sl = classes.index("SL")
    first_g = classes.index("G")
    assert all(c == "S" for c in classes[:first_sl])
    assert all(c == "SL" for c in classes[first_sl:first_g])
    langs = [r["language"] for r in rows[first_g:]]
    assert langs == ["en"] * 18 + ["de"] * 18


def test_max_answers_on_reference_row_only(fixture_survey):
    """Attributes are language-independent; writing max_answers on every
    language's Q row would store the attribute twice. Only the reference
    row carries it."""
    rows = [
        r for r in _rows(to_tsv(fixture_survey)) if r["class"] == "Q" and r["name"] == "priorities"
    ]
    by_lang = {r["language"]: r["max_answers"] for r in rows}
    assert by_lang == {"en": "2", "de": ""}


def test_group_rows_carry_group_number_and_description(fixture_survey):
    """G rows put the 1-based group number in type/scale (the importer's
    key for linking translations) and the description, or nothing, in
    text."""
    rows = [r for r in _rows(to_tsv(fixture_survey)) if r["class"] == "G" and r["language"] == "de"]
    assert [(r["type/scale"], r["name"], r["text"]) for r in rows] == [
        ("1", "Über dich", "Zwei Fragen zu dir."),
        ("2", "Nutzung", ""),
    ]


def test_choice_rows(fixture_survey):
    """Multiple-choice options are SQ rows coded SQ001..; single and ranking
    options are A rows coded A1.. with scale 0. Choice text is escaped."""
    rows = _rows(to_tsv(fixture_survey))
    en = [r for r in rows if r["language"] == "en"]
    sq = [(r["type/scale"], r["name"], r["text"]) for r in en if r["class"] == "SQ"]
    assert sq == [("", "SQ001", "GNU/Linux"), ("", "SQ002", "macOS"), ("", "SQ003", "Windows")]
    a = [(r["type/scale"], r["name"], r["text"]) for r in en if r["class"] == "A"]
    assert a[:2] == [("0", "A1", "Europe"), ("0", "A2", "Asia")]
    assert a[-1] == ("0", "A3", "Docs &amp; manuals")


def test_q_row_cells_left_empty_for_importer_defaults(fixture_survey):
    """Cells we do not own stay empty so the importer applies its defaults.
    A filled id, related_id or encrypted cell would be stored as a stray
    question attribute. relevance is always 1 (always shown)."""
    for r in _rows(to_tsv(fixture_survey)):
        if r["class"] == "Q":
            assert r["id"] == "" and r["related_id"] == "" and r["encrypted"] == ""
            assert r["same_default"] == "" and r["same_script"] == ""
            assert r["default"] == "" and r["validation"] == ""
            assert r["relevance"] == "1"


def test_single_language_survey_omits_additional_languages_and_endtext(tmp_path, fixtures_dir):
    """With one language and no end text, the additional_languages S row
    and the surveyls_endtext SL row are omitted rather than written empty."""
    src = fixtures_dir / "limesurvey"
    structure = (
        (src / "survey.toml")
        .read_text(encoding="utf-8")
        .replace('languages = ["en", "de"]', 'languages = ["en"]')
    )
    en = (
        (src / "survey.en.toml")
        .read_text(encoding="utf-8")
        .replace('end = "<p>Thanks for taking part.</p>"\n', "")
    )
    (tmp_path / "survey.toml").write_text(structure, encoding="utf-8")
    (tmp_path / "survey.en.toml").write_text(en, encoding="utf-8")
    rows = _rows(to_tsv(load_survey(tmp_path / "survey.toml")))
    names = {(r["class"], r["name"]) for r in rows}
    assert ("S", "additional_languages") not in names
    assert ("SL", "surveyls_endtext") not in names
    assert {r["language"] for r in rows if r["class"] in ("G", "Q", "SQ", "A")} == {"en"}


def test_double_quotes_survive_csv_quoting(tmp_path, fixtures_dir):
    """A double quote inside a prompt or inside intro HTML is preserved:
    the csv layer quotes the cell and doubles the inner quotes, and the
    importer's fgetcsv undoes exactly that."""
    src = fixtures_dir / "limesurvey"
    structure = (
        (src / "survey.toml")
        .read_text(encoding="utf-8")
        .replace('languages = ["en", "de"]', 'languages = ["en"]')
    )
    en = (src / "survey.en.toml").read_text(encoding="utf-8")
    en = en.replace(
        'intro = "<p>Welcome to the fixture survey.</p>"',
        "intro = '<p>See <a href=\"https://nixos.org\">nixos.org</a></p>'",
    )
    en = en.replace('prompt = "Anything else?"', "prompt = 'Run \"nix --version\" and tell us.'")
    (tmp_path / "survey.toml").write_text(structure, encoding="utf-8")
    (tmp_path / "survey.en.toml").write_text(en, encoding="utf-8")
    tsv = to_tsv(load_survey(tmp_path / "survey.toml"))
    rows = _rows(tsv)
    intro = next(r["text"] for r in rows if r["name"] == "surveyls_welcometext")
    assert intro == '<p>See <a href="https://nixos.org">nixos.org</a></p>'
    prompt = next(r["text"] for r in rows if r["class"] == "Q" and r["name"] == "feedback")
    assert prompt == 'Run "nix --version" and tell us.'
    assert (
        'href=""https://nixos.org""' in tsv
    )  # the raw file doubles inner quotes inside a quoted cell
