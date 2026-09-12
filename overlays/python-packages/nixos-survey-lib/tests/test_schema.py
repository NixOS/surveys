"""Tests for nixos_survey_lib.schema, the TOML survey definition loader.

The first half covers the structure file (survey.toml), the second half the
per-language text files and load_survey. Every rule has one case here. Most
cases start from VALID_STRUCTURE, VALID_EN or VALID_DE and change exactly
one thing, so a failing case points at the rule that broke.
"""

import textwrap
from pathlib import Path

import pytest
from nixos_survey_lib.schema import (
    Question,
    Survey,
    SurveyError,
    load_structure,
    load_survey,
    text_file_path,
)

# A structure file that satisfies every rule. Tests derive their inputs from
# it with str.replace, so each line it contains should be distinctive enough
# to target on its own.
VALID_STRUCTURE = """
[survey]
id = 2025
language = "en"
languages = ["en"]

[survey.privacy]
anonymized = true
save_ip_address = false
save_referrer = false
date_stamp = false
save_timings = false

[[groups]]
id = "aboutYou"

[[groups.questions]]
id = "country"
type = "single"
choices = ["europe", "asia"]

[[groups.questions]]
id = "os"
type = "multiple"
other = true
mandatory = "soft"
max_answers = 2
choices = ["linux", "macos", "windows"]

[[groups.questions]]
id = "priorities"
type = "ranking"
max_answers = 2
choices = ["perf", "docs"]

[[groups.questions]]
id = "nixVersion"
type = "text"
size = "short"
"""


def _write(tmp_path: Path, text: str, name: str = "survey.toml") -> Path:
    """Write ``text``, dedented, to ``tmp_path/name`` and return the path."""
    p = tmp_path / name
    p.write_text(textwrap.dedent(text), encoding="utf-8")
    return p


def _structure_with(tmp_path: Path, replace: str, by: str) -> Path:
    """Write VALID_STRUCTURE with one substring swapped for another.

    The assert guards against a typo in ``replace``: str.replace silently
    does nothing when the substring is absent, which would leave the file
    valid and make the test fail for the wrong reason.
    """
    assert replace in VALID_STRUCTURE, replace
    return _write(tmp_path, VALID_STRUCTURE.replace(replace, by))


def test_load_structure_valid(tmp_path):
    """A rule-abiding file loads, and every field, flag and default lands on
    the expected dataclass attribute."""
    s = load_structure(_write(tmp_path, VALID_STRUCTURE))
    assert s.id == 2025
    assert s.language == "en"
    assert s.languages == ["en"]
    assert s.privacy.anonymized is True
    assert s.privacy.save_timings is False
    assert [g.id for g in s.groups] == ["aboutYou"]
    qs = s.groups[0].questions
    assert [q.id for q in qs] == ["country", "os", "priorities", "nixVersion"]
    assert qs[0].type == "single" and qs[0].display == "radio"
    assert qs[0].mandatory == "off" and qs[0].other is False
    assert qs[0].choice_keys == ["europe", "asia"]
    assert qs[1].other is True and qs[1].mandatory == "soft" and qs[1].max_answers == 2
    assert qs[2].max_answers == 2
    assert qs[3].size == "short" and qs[3].choice_keys is None


def test_load_structure_missing_file(tmp_path):
    """A missing file is reported as SurveyError naming the file, not as a
    bare FileNotFoundError, so the CLI can print it without a traceback."""
    with pytest.raises(SurveyError, match="survey.toml"):
        load_structure(tmp_path / "survey.toml")


def test_load_structure_toml_syntax_error(tmp_path):
    """A TOML syntax error is wrapped in SurveyError for the same reason."""
    with pytest.raises(SurveyError, match="survey.toml"):
        load_structure(_write(tmp_path, "[survey\nid = 1"))


@pytest.mark.parametrize(
    "replace, by, match",
    [
        pytest.param("id = 2025\n", "", "id", id="missing-id"),
        pytest.param("id = 2025", 'id = "2025"', "id", id="id-not-an-integer"),
        pytest.param("id = 2025", "id = 1", "id", id="id-below-two"),
        pytest.param('language = "en"\n', "", "language", id="missing-language"),
        pytest.param('language = "en"', 'language = "fr"', "languages", id="language-not-listed"),
        pytest.param('languages = ["en"]', "languages = []", "languages", id="languages-empty"),
        pytest.param(
            'languages = ["en"]', 'languages = ["en", "en"]', "languages", id="languages-duplicate"
        ),
        pytest.param(
            'languages = ["en"]',
            'languages = ["en", "EN-us"]',
            "language code",
            id="bad-language-code",
        ),
        pytest.param("anonymized = true\n", "", "anonymized", id="missing-privacy-flag"),
        pytest.param(
            "anonymized = true", 'anonymized = "yes"', "anonymized", id="privacy-flag-not-bool"
        ),
        pytest.param(
            "save_timings = false",
            "save_timings = false\nextra = true",
            "extra",
            id="extra-privacy-key",
        ),
        pytest.param(
            "[survey]\nid = 2025",
            "[survey]\nid = 2025\ncolour = 1",
            "colour",
            id="unknown-survey-key",
        ),
    ],
)
def test_load_structure_survey_table_errors(tmp_path, replace, by, match):
    """Each [survey] and [survey.privacy] rule rejects a file that breaks only
    that rule, and the message names the offending key."""
    with pytest.raises(SurveyError, match=match):
        load_structure(_structure_with(tmp_path, replace, by))


def test_load_structure_language_code_with_two_hyphens_is_valid(tmp_path):
    """LimeSurvey ships codes such as zh-Hant-TW, so a second hyphenated
    segment must pass the language-code pattern."""
    s = load_structure(
        _structure_with(tmp_path, 'languages = ["en"]', 'languages = ["en", "zh-Hant-TW"]')
    )
    assert s.languages == ["en", "zh-Hant-TW"]


@pytest.mark.parametrize(
    "replace, by, match",
    [
        pytest.param('id = "aboutYou"\n', "", "group", id="missing-group-id"),
        pytest.param(
            'id = "aboutYou"', 'id = "about you"', "aboutYou|about you", id="bad-group-id-pattern"
        ),
        pytest.param(
            'id = "aboutYou"',
            'id = "aboutYou"\ntitle = "x"',
            "title",
            id="text-key-in-structure-group",
        ),
    ],
)
def test_load_structure_group_errors(tmp_path, replace, by, match):
    """Group rules: the id is required and follows the id pattern, and no
    text (such as a title) belongs in the structure file."""
    with pytest.raises(SurveyError, match=match):
        load_structure(_structure_with(tmp_path, replace, by))


def test_load_structure_question_without_id_names_its_group(tmp_path):
    """A question with no id cannot be named in the error, so the message
    names the group it sits in instead."""
    with pytest.raises(SurveyError, match="aboutYou"):
        load_structure(_structure_with(tmp_path, 'id = "country"\n', ""))


def test_load_structure_duplicate_group_id_case_insensitive(tmp_path):
    """Group ids are unique regardless of case, matching the question-id
    rule, so ABOUTYOU collides with aboutYou."""
    text = (
        VALID_STRUCTURE
        + '\n[[groups]]\nid = "ABOUTYOU"\n\n[[groups.questions]]\nid = "extra"\ntype = "text"\n'
    )
    with pytest.raises(SurveyError, match="ABOUTYOU"):
        load_structure(_write(tmp_path, text))


def test_load_structure_no_groups(tmp_path):
    """A survey needs at least one group; LimeSurvey has no questions
    outside groups."""
    text = VALID_STRUCTURE.split("[[groups]]")[0]
    with pytest.raises(SurveyError, match="group"):
        load_structure(_write(tmp_path, text))


def test_load_structure_group_without_questions(tmp_path):
    """An empty group would import as an empty page; reject it."""
    text = VALID_STRUCTURE + '\n[[groups]]\nid = "empty"\n'
    with pytest.raises(SurveyError, match="empty"):
        load_structure(_write(tmp_path, text))


@pytest.mark.parametrize(
    "replace, by, match",
    [
        pytest.param('id = "country"', 'id = "1country"', "1country", id="id-starts-with-digit"),
        pytest.param(
            'id = "country"',
            'id = "countryOfResidenceLong"',
            "countryOfResidenceLong",
            id="id-over-20-chars",
        ),
        pytest.param('id = "country"', 'id = "country_x"', "country_x", id="id-with-underscore"),
        pytest.param('id = "country"', 'id = "Token"', "reserved", id="id-is-reserved-word"),
        pytest.param('id = "country"', 'id = "OS"', "OS", id="duplicate-id-case-insensitive"),
        pytest.param('id = "os"', 'id = "country"', "country", id="duplicate-id-exact"),
        pytest.param(
            'id = "os"\ntype = "multiple"',
            'id = "os"\ntype = "multiple"\ndisplay = "radio"',
            "display",
            id="display-on-multiple",
        ),
        pytest.param(
            'id = "country"\ntype = "single"',
            'id = "country"\ntype = "radio"',
            "type",
            id="bad-type",
        ),
        pytest.param(
            'id = "country"\ntype = "single"',
            'id = "country"\ntype = "single"\nprompt = "x"',
            "prompt",
            id="text-key-in-structure-question",
        ),
        pytest.param(
            'id = "country"\ntype = "single"',
            'id = "country"\ntype = "single"\nmandatory = "yes"',
            "mandatory",
            id="bad-mandatory",
        ),
        pytest.param(
            'id = "country"\ntype = "single"',
            'id = "country"\ntype = "single"\ndisplay = "list"',
            "display",
            id="bad-display",
        ),
        pytest.param(
            'id = "country"\ntype = "single"',
            'id = "country"\ntype = "single"\nmax_answers = 1',
            "max_answers",
            id="max-answers-on-single",
        ),
        pytest.param(
            'id = "country"\ntype = "single"',
            'id = "country"\ntype = "single"\nsize = "short"',
            "size",
            id="size-on-single",
        ),
        pytest.param('choices = ["europe", "asia"]', "choices = []", "choices", id="choices-empty"),
        pytest.param(
            'choices = ["europe", "asia"]',
            'choices = ["europe", "Europe"]',
            "Europe",
            id="duplicate-choice-key-case-insensitive",
        ),
        pytest.param(
            'choices = ["europe", "asia"]',
            'choices = ["europe", "9asia"]',
            "9asia",
            id="bad-choice-key-pattern",
        ),
        pytest.param(
            'choices = ["europe", "asia"]\n', "", "choices", id="missing-choices-on-single"
        ),
        pytest.param(
            'id = "nixVersion"\ntype = "text"',
            'id = "nixVersion"\ntype = "text"\nchoices = ["a"]',
            "choices",
            id="choices-on-text",
        ),
        pytest.param(
            'id = "nixVersion"\ntype = "text"',
            'id = "nixVersion"\ntype = "text"\nother = true',
            "other",
            id="other-on-text",
        ),
        pytest.param(
            'id = "priorities"\ntype = "ranking"',
            'id = "priorities"\ntype = "ranking"\nother = true',
            "other",
            id="other-on-ranking",
        ),
        pytest.param(
            'max_answers = 2\nchoices = ["perf", "docs"]',
            'max_answers = 3\nchoices = ["perf", "docs"]',
            "max_answers",
            id="max-answers-over-choice-count",
        ),
        pytest.param(
            'max_answers = 2\nchoices = ["perf", "docs"]',
            'max_answers = 0\nchoices = ["perf", "docs"]',
            "max_answers",
            id="max-answers-zero",
        ),
    ],
)
def test_load_structure_question_errors(tmp_path, replace, by, match):
    """Each question rule rejects a file that breaks only that rule: the id
    pattern and reserved words LimeSurvey enforces, uniqueness, per-type
    fields, and choice-key rules."""
    with pytest.raises(SurveyError, match=match):
        load_structure(_structure_with(tmp_path, replace, by))


def test_load_structure_error_names_file_and_question(tmp_path):
    """Error messages carry the file name and the question id so an author
    with forty questions can find the culprit."""
    p = _structure_with(
        tmp_path,
        'id = "country"\ntype = "single"',
        'id = "country"\ntype = "single"\nsize = "short"',
    )
    with pytest.raises(SurveyError) as exc:
        load_structure(p)
    assert "survey.toml" in str(exc.value)
    assert "country" in str(exc.value)


# --- text files and load_survey ---------------------------------------------
#
# The text-file tests start from two complete language files, VALID_EN and
# VALID_DE, and follow the same one-change-per-case pattern as above.

VALID_EN = """
[survey]
title = "Tiny Survey"
intro = "<p>Welcome.</p>"
end = "<p>Thanks.</p>"

[groups.aboutYou]
title = "About you"
description = "Some questions about you."

[questions.country]
prompt = "Where do you live?"
choices.europe = "Europe"
choices.asia = "Asia"

[questions.os]
prompt = "Which operating systems do you use?"
help = "Pick all that apply."
choices.linux = "GNU/Linux"
choices.macos = "macOS"
choices.windows = "Windows"

[questions.priorities]
prompt = "Rank your priorities."
choices.docs = "Documentation"
choices.perf = "Performance"

[questions.nixVersion]
prompt = "Which version of Nix do you use?"
"""

VALID_DE = """
[survey]
title = "Kleine Umfrage"
intro = "<p>Willkommen.</p>"
end = "<p>Danke.</p>"

[groups.aboutYou]
title = "Über dich"
description = "Einige Fragen zu dir."

[questions.country]
prompt = "Wo lebst du?"
choices.europe = "Europa"
choices.asia = "Asien"

[questions.os]
prompt = "Welche Betriebssysteme nutzt du?"
help = "Mehrfachauswahl möglich."
choices.linux = "GNU/Linux"
choices.macos = "macOS"
choices.windows = "Windows"

[questions.priorities]
prompt = "Ordne deine Prioritäten."
choices.perf = "Leistung"
choices.docs = "Dokumentation"

[questions.nixVersion]
prompt = "Welche Nix-Version nutzt du?"
"""


def _survey_dir(
    tmp_path: Path, *, en: str = VALID_EN, de: str | None = None, structure: str = VALID_STRUCTURE
) -> Path:
    """Write a complete survey directory and return the structure path.

    With ``de`` given, the structure's language list is widened to include
    German and a survey.de.toml is written beside survey.en.toml.
    """
    if de is not None:
        structure = structure.replace('languages = ["en"]', 'languages = ["en", "de"]')
    p = _write(tmp_path, structure)
    _write(tmp_path, en, "survey.en.toml")
    if de is not None:
        _write(tmp_path, de, "survey.de.toml")
    return p


def test_text_file_path():
    """Text files sit beside the structure file as <stem>.<lang>.toml."""
    assert text_file_path(Path("/x/survey.toml"), "de") == Path("/x/survey.de.toml")
    assert text_file_path(Path("/x/tiny_survey.toml"), "en") == Path("/x/tiny_survey.en.toml")


def test_load_survey_resolves_reference_language(tmp_path):
    """load_survey copies the reference language's text onto Survey, Group
    and Question so downstream code (loader, process.py) reads plain
    strings, while the structure fields come through unchanged."""
    s = load_survey(_survey_dir(tmp_path, de=VALID_DE))
    assert isinstance(s, Survey)
    assert s.id == 2025 and s.language == "en" and s.languages == ["en", "de"]
    assert s.title == "Tiny Survey" and s.intro == "<p>Welcome.</p>" and s.end == "<p>Thanks.</p>"
    g = s.groups[0]
    assert g.id == "aboutYou" and g.title == "About you"
    assert g.description == "Some questions about you."
    q = {q.id: q for q in s.questions}
    assert isinstance(q["country"], Question)
    assert q["country"].prompt == "Where do you live?"
    assert q["country"].choices == ["Europe", "Asia"]
    assert q["country"].choice_keys == ["europe", "asia"]
    assert q["os"].help == "Pick all that apply."
    assert q["os"].other is True and q["os"].mandatory == "soft" and q["os"].max_answers == 2
    assert q["nixVersion"].choices is None and q["nixVersion"].help is None
    assert q["nixVersion"].size == "short"
    assert q["country"].csv_columns == []


def test_load_survey_choices_follow_structure_order_not_file_order(tmp_path):
    """Choice order is the structure file's order. Text files may list the
    keys in any order; this is what keeps translated answers lined up by
    position in the LimeSurvey import."""
    s = load_survey(_survey_dir(tmp_path, de=VALID_DE))
    q = {q.id: q for q in s.questions}
    # Structure lists ["perf", "docs"]; the text files list docs first or second.
    assert q["priorities"].choices == ["Performance", "Documentation"]
    assert s.texts["de"].questions["priorities"].choices == ["Leistung", "Dokumentation"]


def test_load_survey_texts_holds_every_language_and_matches_resolved(tmp_path):
    """Survey.texts carries every language, reference included, and the
    resolved fields are exactly the reference language's entries."""
    s = load_survey(_survey_dir(tmp_path, de=VALID_DE))
    assert set(s.texts) == {"en", "de"}
    ref = s.texts["en"]
    assert ref.title == s.title and ref.intro == s.intro and ref.end == s.end
    assert ref.groups["aboutYou"].title == s.groups[0].title
    assert ref.questions["country"].prompt == s.questions[0].prompt
    assert s.texts["de"].title == "Kleine Umfrage"
    assert s.texts["de"].questions["os"].help == "Mehrfachauswahl möglich."


def test_load_survey_single_language(tmp_path):
    """A single-language survey is the common case and needs no German file."""
    s = load_survey(_survey_dir(tmp_path))
    assert s.languages == ["en"] and set(s.texts) == {"en"}


def test_load_survey_missing_text_file(tmp_path):
    """A language listed in the structure without a text file is an error
    naming the expected file."""
    p = _write(tmp_path, VALID_STRUCTURE)
    with pytest.raises(SurveyError, match="survey.en.toml"):
        load_survey(p)


def test_load_survey_rejects_text_file_for_unlisted_language(tmp_path):
    """A stray survey.de.toml when only English is listed is most likely a
    forgotten entry in ``languages``; fail rather than ignore it."""
    p = _survey_dir(tmp_path)
    _write(tmp_path, VALID_DE, "survey.de.toml")
    with pytest.raises(SurveyError, match="survey.de.toml"):
        load_survey(p)


def test_load_survey_text_file_syntax_error(tmp_path):
    """TOML syntax errors in a text file surface as SurveyError too."""
    p = _survey_dir(tmp_path, en="[survey\ntitle = 1")
    with pytest.raises(SurveyError, match="survey.en.toml"):
        load_survey(p)


@pytest.mark.parametrize(
    "replace, by, match",
    [
        pytest.param('title = "Tiny Survey"\n', "", "title", id="missing-title"),
        pytest.param('intro = "<p>Welcome.</p>"\n', "", "intro", id="missing-intro"),
        pytest.param('title = "Tiny Survey"', 'title = ""', "title", id="empty-title"),
        pytest.param('title = "Tiny Survey"', 'title = "   "', "title", id="whitespace-only-title"),
        pytest.param(
            'title = "Tiny Survey"',
            'title = "\\"Quoted\\""',
            "double quote",
            id="title-wrapped-in-quotes",
        ),
        pytest.param(
            'title = "Tiny Survey"',
            'title = " \\"Other\\" "',
            "double quote",
            id="padded-title-wrapped-in-quotes",
        ),
        pytest.param(
            'end = "<p>Thanks.</p>"',
            'end = "<p>Thanks.</p>"\nfooter = "x"',
            "footer",
            id="unknown-survey-key",
        ),
        pytest.param(
            "[groups.aboutYou]\n",
            "[groups.aboutYou]\ncolour = 1\n",
            "colour",
            id="unknown-group-key",
        ),
        pytest.param(
            '[groups.aboutYou]\ntitle = "About you"\ndescription = "Some questions about you."\n',
            "",
            "groups",
            id="missing-groups-table",
        ),
        pytest.param(
            "[groups.aboutYou]",
            "[groups.somethingElse]",
            "aboutYou|somethingElse",
            id="group-table-for-unknown-id",
        ),
        pytest.param(
            "[groups.aboutYou]\ntitle",
            "[groups.aboutYou]\nnotitle",
            "title|notitle",
            id="missing-group-title",
        ),
        pytest.param(
            '[questions.nixVersion]\nprompt = "Which version of Nix do you use?"\n',
            "",
            "nixVersion",
            id="missing-question-table",
        ),
        pytest.param(
            "[questions.nixVersion]",
            '[questions.nixVersionX]\nprompt = "x"\n\n[questions.nixVersion]',
            "nixVersionX",
            id="question-table-for-unknown-id",
        ),
        pytest.param(
            'prompt = "Which version of Nix do you use?"',
            'prompt = "Which version of Nix do you use?"\nchoices.a = "A"',
            "choices",
            id="choices-on-text-question",
        ),
        pytest.param(
            'prompt = "Which version of Nix do you use?"',
            'prompt = "Which version of Nix do you use?"\ntype = "text"',
            "type",
            id="structure-key-in-text-file",
        ),
        pytest.param('prompt = "Where do you live?"\n', "", "prompt", id="missing-prompt"),
        pytest.param('choices.asia = "Asia"\n', "", "asia", id="missing-choice-key"),
        pytest.param(
            'choices.asia = "Asia"',
            'choices.asia = "Asia"\nchoices.africa = "Africa"',
            "africa",
            id="extra-choice-key",
        ),
        pytest.param('choices.asia = "Asia"', 'choices.asia = ""', "asia", id="empty-choice-text"),
    ],
)
def test_load_survey_text_file_errors(tmp_path, replace, by, match):
    """Each text-file rule rejects an English file that breaks only that
    rule: required and unknown keys, empty text, the double-quote quirk,
    and table or choice-key sets that disagree with the structure."""
    assert replace in VALID_EN, replace
    p = _survey_dir(tmp_path, en=VALID_EN.replace(replace, by))
    with pytest.raises(SurveyError, match=match):
        load_survey(p)


@pytest.mark.parametrize(
    "en_replace, en_by, de_replace, de_by, match",
    [
        pytest.param(
            "",
            "",
            'prompt = "Wo lebst du?"',
            'prompt = "Wo lebst du?"\nhelp = "Hilfe"',
            "help",
            id="help-in-de-only",
        ),
        pytest.param(
            "", "", 'help = "Mehrfachauswahl möglich."\n', "", "help", id="help-in-en-only"
        ),
        pytest.param("", "", 'end = "<p>Danke.</p>"\n', "", "end", id="end-in-en-only"),
        pytest.param('end = "<p>Thanks.</p>"\n', "", "", "", "end", id="end-in-de-only"),
        pytest.param(
            "",
            "",
            'description = "Einige Fragen zu dir."\n',
            "",
            "description",
            id="description-in-en-only",
        ),
        pytest.param(
            'description = "Some questions about you."\n',
            "",
            "",
            "",
            "description",
            id="description-in-de-only",
        ),
    ],
)
def test_load_survey_optional_text_must_match_reference(
    tmp_path, en_replace, en_by, de_replace, de_by, match
):
    """Optional text (help, end, group description) is present in every
    language or in none; the reference language decides. A translation that
    silently lacks a help text would otherwise go unnoticed."""
    en = VALID_EN.replace(en_replace, en_by) if en_replace else VALID_EN
    de = VALID_DE.replace(de_replace, de_by) if de_replace else VALID_DE
    p = _survey_dir(tmp_path, en=en, de=de)
    with pytest.raises(SurveyError, match=match):
        load_survey(p)


def test_load_survey_error_names_language_file_and_id(tmp_path):
    """Text-file errors name the language file, the question and the choice
    key, so a translator can find the gap."""
    de = VALID_DE.replace('choices.asia = "Asien"\n', "")
    p = _survey_dir(tmp_path, de=de)
    with pytest.raises(SurveyError) as exc:
        load_survey(p)
    assert "survey.de.toml" in str(exc.value)
    assert "country" in str(exc.value)
    assert "asia" in str(exc.value)


def test_load_survey_strips_surrounding_whitespace(tmp_path):
    """Text values lose leading and trailing whitespace, so a multi-line
    TOML string does not carry a trailing newline into a prompt."""
    en = VALID_EN.replace('title = "Tiny Survey"', 'title = "  Tiny  "')
    assert load_survey(_survey_dir(tmp_path, en=en)).title == "Tiny"


def test_question_defaults_allow_legacy_construction():
    """Existing code (normalize.py, older tests) builds Question with the
    original five fields; the new fields must default sensibly."""
    q = Question(id="x", prompt="X?", type="single", choices=["a"], csv_columns=["X?"])
    assert q.help is None and q.mandatory == "off" and q.other is False
    assert q.display == "radio" and q.max_answers is None and q.size == "long"
    assert q.choice_keys is None
