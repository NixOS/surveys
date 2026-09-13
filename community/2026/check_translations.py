"""Checks on translated text that load_survey cannot make.

load_survey enforces structure: every group, question, prompt and choice label
present, no extras, optional text matching English. That leaves the content
unchecked, and the failure mode of a generated translation is a fluent wrong
value rather than a missing one. These are the mechanical subset of "wrong"
worth catching before a human reads the file.

Fails on two rules that are unambiguous: formal-register pronouns, and product
names dropped in translation. Everything else prints as a NOTE to judge by eye.

Usage: check_translations.py [survey.toml]
"""

import re
import sys
from pathlib import Path

from nixos_survey_lib.schema import load_survey

# Formality slips. The questions address the respondent informally and so does
# LimeSurvey's own chrome, from the locale; a formal pronoun here makes the two
# disagree inside one page. See community/TRANSLATING.md.
FORMAL = {
    "fr": ["vous", "votre", "vos"],
    "es-informal": ["usted", "ustedes"],
    "de-informal": ["Sie", "Ihnen", "Ihre", "Ihrem", "Ihren"],
    "zh-Hans": ["您"],
}

# Names that must survive translation. Compared case-insensitively: German
# capitalises nouns, so "overlays" correctly becomes "Overlays".
PRODUCTS = [
    "Nix",
    "Nixpkgs",
    "NixOS",
    "Lix",
    "Snix",
    "Tvix",
    "Determinate Nix",
    "stdenv",
    "flake",
    "overlay",
]


def contains(value: str, word: str) -> bool:
    """Whole-word match for Latin scripts, substring for CJK.

    A space-delimited test would miss every sentence-final pronoun ("Wie alt
    bist du?"), miss French inversion ("Utilises-tu"), and never match in
    Chinese, which has no spaces. Unicode word boundaries do not help for CJK
    either, since those characters are themselves word characters.
    """
    if word.isascii():
        return re.search(rf"(?<!\w){re.escape(word)}(?!\w)", value) is not None
    return word in value


def strings(texts, keys_by_qid):
    """Every translatable value in one language, keyed uniquely.

    The key identifies the individual choice. Keying every choice of a question
    the same way would collapse the reference mapping to one arbitrary label
    per question and make the comparison below a no-op.
    """
    yield "[survey] title", texts.title
    yield "[survey] intro", texts.intro
    for gid, group in texts.groups.items():
        yield f"[groups.{gid}] title", group.title
    for qid, question in texts.questions.items():
        yield f"[questions.{qid}] prompt", question.prompt
        for key, label in zip(keys_by_qid.get(qid) or [], question.choices or []):
            yield f"[questions.{qid}] choices.{key}", label


def main(path: str) -> int:
    """Report every failure rather than stopping at the first, so one run
    tells a translator everything to fix."""
    survey = load_survey(Path(path))
    keys_by_qid = {q.id: q.choice_keys for g in survey.groups for q in g.questions}
    reference = survey.texts[survey.language]
    english = dict(strings(reference, keys_by_qid))
    failures = 0

    for language, texts in survey.texts.items():
        if language == survey.language:
            continue
        for where, value in strings(texts, keys_by_qid):
            for word in FORMAL.get(language, []):
                if contains(value, word):
                    print(f"{language}: formal register {word!r} in {where}: {value}")
                    failures += 1
            source = english.get(where)
            if source is None:
                continue
            for product in PRODUCTS:
                if product.lower() in source.lower() and product.lower() not in value.lower():
                    print(f"{language}: {product!r} dropped in {where}: {value}")
                    failures += 1
            if source == value and len(source.split()) > 3:
                print(f"{language}: NOTE possibly untranslated {where}: {value}")
        if texts.intro.count("<p>") != reference.intro.count("<p>"):
            print(
                f"{language}: intro has {texts.intro.count('<p>')} paragraphs, "
                f"{survey.language} has {reference.intro.count('<p>')}"
            )
            failures += 1

    print(f"{failures} failures")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if sys.argv[1:] else "survey.toml"))
