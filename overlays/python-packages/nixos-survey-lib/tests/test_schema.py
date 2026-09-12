"""Tests for nixos_survey_lib.schema, the TOML survey definition loader.

This first half covers the structure file (survey.toml). Every rule in the
spec's "Structure file" section has one case here. Most cases start from
VALID_STRUCTURE and change exactly one thing, so a failing case points at
the rule that broke. The second half, appended in the next task, covers the
per-language text files and load_survey.
"""

import textwrap
from pathlib import Path

import pytest
from nixos_survey_lib.schema import (
    SurveyError,
    load_structure,
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
