"""Assert the 2026 instrument matches its design spec.

Runs in the checkPhase of nixos-surveys-community-2026-limesurvey, so
`nix build` fails on any drift. Everything asserted here is a decision from
docs/superpowers/specs/2026-09-13-community-survey-2026-design.md that would
otherwise only be caught by a human rereading the TOML.

The derivation's src is community/, not community/2026/, so that the
carried-verbatim questions can be compared against last year's file.
"""

from pathlib import Path

import pytest
from nixos_survey_lib.schema import load_survey

HERE = Path(__file__).parent

# The nine questions the spec carries forward untouched. Byte-equality with
# 2025 is their only correctness criterion, and about 200 choice labels are
# retyped by hand to produce them.
CARRIED_VERBATIM = (
    "age",
    "firstHeardWhich",
    "firstHeardHow",
    "involvement",
    "operatingSystems",
    "nixOnOs",
    "targetTriple",
    "infrastructure",
    "experimentalFeatures",
)


@pytest.fixture(scope="module")
def survey():
    return load_survey(HERE / "survey.toml")


@pytest.fixture(scope="module")
def survey_2025():
    """Last year's instrument, for the byte-equality and type checks."""
    return load_survey(HERE.parent / "2025" / "survey.toml")


def questions(survey):
    """Every question by id, flattened across groups."""
    return {q.id: q for g in survey.groups for q in g.questions}


def test_survey_level_settings(survey):
    """Privacy flags are fixed at activation and cannot be changed after."""
    assert survey.id == 2026
    assert survey.language == "en"
    assert survey.privacy.anonymized is True
    assert survey.privacy.save_ip_address is False
    assert survey.privacy.save_referrer is False
    assert survey.privacy.date_stamp is False
    assert survey.privacy.save_timings is False


def test_ids_are_unique_and_within_limesurveys_limit(survey):
    """LimeSurvey's Question model caps the question code at 20 characters and
    schema.py enforces it at load time, so the length half can only fail if
    ID_RE changes. Uniqueness is the half worth asserting: ids are typed by
    hand across five tasks and a duplicate silently merges two questions."""
    ids = [q.id for g in survey.groups for q in g.questions]
    assert len(ids) == len(set(ids))
    assert [i for i in ids if len(i) > 20] == []


def test_carried_questions_are_byte_identical_to_2025(survey, survey_2025):
    """Nine questions are copied from 2025 unchanged, and with them about 200
    choice labels are retyped into a new file. Nothing else in this suite
    would notice a dropped comma. Ids not yet added are skipped, so this grows
    with the instrument."""
    old, new = questions(survey_2025), questions(survey)
    for qid in CARRIED_VERBATIM:
        if qid not in new:
            continue
        a, b = old[qid], new[qid]
        assert b.type == a.type, qid
        assert b.prompt == a.prompt, qid
        assert b.choice_keys == a.choice_keys, qid
        assert b.choices == a.choices, qid


def test_changed_questions_keep_their_2025_type(survey, survey_2025):
    """The spec changes exactly one question's type: nixVersion, text to
    single. Every other question carried forward keeps the type it had, and
    two are easy to get wrong because their prompts read like single-answer
    questions: installMethod and hardwareConfig are both multiple. Typing
    either as single silently ends its 2025 series and the build stays green.
    """
    old = {qid: q.type for qid, q in questions(survey_2025).items()}
    changed = {"nixVersion": ("text", "single")}
    for qid, q in questions(survey).items():
        if qid not in old:
            continue
        if qid in changed:
            assert (old[qid], q.type) == changed[qid], qid
        else:
            assert q.type == old[qid], f"{qid}: 2025 is {old[qid]}, 2026 is {q.type}"


def test_about_you_group(survey):
    group = next(g for g in survey.groups if g.id == "aboutYou")
    assert [q.id for q in group.questions] == [
        "age",
        "genderIdentity",
        "transgender",
        "yearsProgramming",
        "country",
        "employment",
        "role",
        "industry",
        "domain",
    ]


def test_country_is_the_only_dropdown_and_sorts_per_language(survey):
    """249 radio buttons is not an alternative, and one fixed order can only
    be alphabetical in one of five languages."""
    dropdowns = [q.id for g in survey.groups for q in g.questions if q.display == "dropdown"]
    assert dropdowns == ["country"]
    country = questions(survey)["country"]
    assert country.alphasort is True
    assert len(country.choices) == 250
    assert country.choice_keys[-1] == "preferNotToSay"


def test_transgender_has_the_four_options_stats_nz_specifies(survey):
    """'yes', 'no', 'don't know', and 'prefer not to say' at a minimum."""
    assert questions(survey)["transgender"].choice_keys == [
        "yes",
        "no",
        "dontKnow",
        "preferNotToSay",
    ]


def test_years_programming_has_no_gap_at_fifty(survey):
    """2025 offered '45 to 49 years' then 'More than 50 years', so exactly 50
    years had no valid answer."""
    q = questions(survey)["yearsProgramming"]
    assert "50 or more years" in q.choices
    assert "More than 50 years" not in q.choices


def test_industry_and_domain_offer_refusal(survey):
    """The only two demographic questions without one in 2025. Inconsistent
    application makes item nonresponse non-comparable."""
    for qid in ("industry", "domain"):
        assert questions(survey)[qid].choice_keys[-1] == "preferNotToSay", qid


def test_industry_has_a_software_sector(survey):
    """The 2025 list had no software or technology sector at all, which is why
    21.0% chose Other."""
    q = questions(survey)["industry"]
    assert "Software development" in q.choices
    assert "notEmployed" in q.choice_keys
    assert len(q.choices) == 29


def test_domain_is_one_axis_and_gained_five(survey):
    """2025 mixed four axes: what the software does, how it is licensed, how
    it is delivered, and who it serves."""
    q = questions(survey)["domain"]
    assert len(q.choices) == 19
    for key in ("desktopSoftware", "buildTooling", "databases", "dataAndMl", "scientificComputing"):
        assert key in q.choice_keys, key
    for gone in ("openSourceSoftware", "softwareAsAService"):
        assert gone not in q.choice_keys, gone


def test_employment_gives_non_workers_somewhere_to_be_counted(survey):
    """Stack Overflow gates industry behind this and never showed it to 31.6%
    of their sample. We cannot branch, so this recovers it at analysis time."""
    q = questions(survey)["employment"]
    assert q.choice_keys == [
        "employed",
        "selfEmployed",
        "notEmployed",
        "student",
        "retired",
        "preferNotToSay",
    ]


def test_role_gained_architect_and_the_non_employment_states(survey):
    """Architect took 6.1% of Stack Overflow's 2025 answers and is absent only
    because we copied their 2024 list."""
    q = questions(survey)["role"]
    for key in ("architect", "selfEmployedOrFounder", "retired", "notEmployed"):
        assert key in q.choice_keys, key
    assert q.choice_keys[-2:] == ["other", "preferNotToSay"]
    assert len(q.choices) == 38


def test_experience_group(survey):
    group = next(g for g in survey.groups if g.id == "experience")
    assert [q.id for q in group.questions] == [
        "firstHeardWhich",
        "firstHeardHow",
        "yearsUsingNix",
        "skillLevel",
        "traits",
        "involvement",
    ]


def test_traits_order_is_frozen(survey):
    """Changing this list's length breaks the 2025 comparison for every item
    in it, so all four additions land in one break and the order then freezes.
    Measuring learning speed means comparing this year's under-one-year cohort
    against last year's, which only works while the retained twelve keep their
    wording."""
    assert questions(survey)["traits"].choice_keys == [
        "iRelyOnExamples",
        "iWriteOwnExpressions",
        "iUseModuleSystem",
        "iWriteOwnModules",
        "iUnderstandModuleDepth",
        "iHaveUsedOverlays",
        "iUnderstandOverlays",
        "iWrittenDerivation",
        "iUnderstandStdenv",
        "iComfortableContributing",
        "iTeachOthers",
        "iMakeArchitecturalChoices",
        "iReadNixSource",
        "iCanDebugBuilds",
        "iUnderstandErrorMessages",
        "noneOfThese",
    ]


def test_traits_keeps_the_joke_and_fixes_the_typo(survey):
    """'I completely understand all Nix error messages' is deliberate and is
    the only extreme-tail marker in the question: 135 selections, 4.0%.
    Softening it to 'usually' would move it to roughly 40% and turn the top of
    the ladder into a mid-ladder item. 'aide' was a misspelling two
    respondents reported."""
    q = questions(survey)["traits"]
    labels = dict(zip(q.choice_keys, q.choices))
    assert labels["iUnderstandErrorMessages"] == "I completely understand all Nix error messages."
    assert "aide" not in labels["iWriteOwnExpressions"]
    assert "without aid." in labels["iWriteOwnExpressions"]


def test_traits_retained_twelve_keep_their_2025_wording(survey, survey_2025):
    """The cohort-versus-cohort comparison this question exists for depends on
    it. Only iWriteOwnExpressions changes, and only to fix a typo."""
    old = dict(
        zip(questions(survey_2025)["traits"].choice_keys, questions(survey_2025)["traits"].choices)
    )
    new = dict(zip(questions(survey)["traits"].choice_keys, questions(survey)["traits"].choices))
    for key, label in old.items():
        if key == "iWriteOwnExpressions":
            assert new[key] == label.replace("aide", "aid")
        else:
            assert new[key] == label, key


def test_terminology_prompts_name_the_package_manager(survey):
    """S2: the intro's paragraph defining Nix is removed, because a technical
    audience resolves an ambiguous term silently and confidently rather than
    asking. Terms are defined in the questions whose answers depend on them."""
    qs = questions(survey)
    for qid in ("yearsUsingNix", "skillLevel"):
        assert "Nix package manager" in qs[qid].prompt, qid
    assert "Round to the nearest whole year" in qs["yearsUsingNix"].prompt
