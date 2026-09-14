"""Emit the country choice keys or labels for community/2026/survey*.toml.

The 249 ISO 3166-1 country names are standard data. Hand-translating them
would spend most of the translation budget on the least valuable strings and
would disagree with what respondents see everywhere else, so they come from
CLDR instead.

Choice keys are ISO alpha-2 codes. They never reach LimeSurvey; they only
link a label across language files (see nixos_survey_lib.schema).

Display order is not this file's problem: `country` sets `alphasort = true`,
so LimeSurvey sorts the options in whichever language it is showing. The
order here is by English name, so the structure file reads sensibly.

Usage:
    generate_countries.py keys            # the survey.toml choices array
    generate_countries.py labels en       # the survey.en.toml choices lines
    generate_countries.py labels zh_Hans  # a babel locale name, not a file suffix
"""

import sys

import pycountry
from babel import Locale

COUNTRIES = sorted(pycountry.countries, key=lambda c: c.name)


def keys() -> str:
    """The choices array for the structure file, preferNotToSay last."""
    lines = [f'  "{c.alpha_2}",' for c in COUNTRIES]
    lines.append('  "preferNotToSay",')
    return "choices = [\n" + "\n".join(lines) + "\n]"


def labels(locale_name: str) -> str:
    """One choices.<key> line per country, in the structure file's order.

    preferNotToSay is not generated: it is survey text, not standard data,
    and each language file writes it by hand.
    """
    locale = Locale.parse(locale_name)
    missing = [c.alpha_2 for c in COUNTRIES if c.alpha_2 not in locale.territories]
    if missing:
        raise SystemExit(f"{locale_name}: no CLDR name for {missing}")
    out = []
    for c in COUNTRIES:
        name = locale.territories[c.alpha_2].replace("\\", "\\\\").replace('"', '\\"')
        out.append(f'choices.{c.alpha_2} = "{name}"')
    return "\n".join(out)


if __name__ == "__main__":
    if sys.argv[1:2] == ["keys"]:
        print(keys())
    elif sys.argv[1:2] == ["labels"] and sys.argv[2:3]:
        print(labels(sys.argv[2]))
    else:
        raise SystemExit(__doc__)
