"""Regenerate expected_survey.txt from hand-written rows. The rows are the
oracle; never derive them from the emitter. Run:
`nix develop -c python3 tests/fixtures/limesurvey/make_expected.py`
"""

import csv
from pathlib import Path

COLS = [
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
    "max_answers",
]


def R(cls, ts="", name="", text="", help="", lang="", rel="", mand="", other="", ma=""):
    """One row: the named cells in COLS order, every other cell empty."""
    d = {
        "class": cls,
        "type/scale": ts,
        "name": name,
        "text": text,
        "help": help,
        "language": lang,
        "relevance": rel,
        "mandatory": mand,
        "other": other,
        "max_answers": ma,
    }
    return [d.get(c, "") for c in COLS]


def S(name, text):
    """An S row: one language-independent survey setting."""
    return R("S", name=name, text=text)


def SL(name, text, lang):
    """An SL row: one survey text in one language."""
    return R("SL", name=name, text=text, lang=lang)


def content(lang, t, ref):
    """The G/Q/SQ/A block for one language. ``ref`` marks the reference
    language, which is the only one carrying the max_answers attribute."""
    g1, g2 = t["groups"]
    q = t["q"]
    ma = "2" if ref else ""
    return [
        R("G", "1", g1[0], g1[1], lang=lang),
        R("Q", "L", "country", q["country"][0], lang=lang, rel="1", mand="N", other="N"),
        R("A", "0", "A1", q["country"][1][0], lang=lang),
        R("A", "0", "A2", q["country"][1][1], lang=lang),
        R("Q", "!", "age", q["age"][0], lang=lang, rel="1", mand="Y", other="N"),
        R("A", "0", "A1", q["age"][1][0], lang=lang),
        R("A", "0", "A2", q["age"][1][1], lang=lang),
        R("G", "2", g2[0], g2[1], lang=lang),
        R("Q", "M", "os", q["os"][0], help=q["os"][2], lang=lang, rel="1", mand="S", other="Y"),
        R("SQ", "", "SQ001", q["os"][1][0], lang=lang),
        R("SQ", "", "SQ002", q["os"][1][1], lang=lang),
        R("SQ", "", "SQ003", q["os"][1][2], lang=lang),
        R(
            "Q",
            "R",
            "priorities",
            q["priorities"][0],
            lang=lang,
            rel="1",
            mand="N",
            other="N",
            ma=ma,
        ),
        R("A", "0", "A1", q["priorities"][1][0], lang=lang),
        R("A", "0", "A2", q["priorities"][1][1], lang=lang),
        R("A", "0", "A3", q["priorities"][1][2], lang=lang),
        R("Q", "S", "nixVersion", q["nixVersion"][0], lang=lang, rel="1", mand="N", other="N"),
        R("Q", "T", "feedback", q["feedback"][0], lang=lang, rel="1", mand="N", other="N"),
    ]


EN = {
    "title": "Tiny LimeSurvey Fixture",
    "intro": "<p>Welcome to the fixture survey.</p>",
    "end": "<p>Thanks for taking part.</p>",
    "groups": [("About you", "Two questions about you."), ("Usage", "")],
    "q": {
        "country": ("Where do you live?", ["Europe", "Asia"]),
        "age": ("How old are you?", ["Under 30", "30 or older"]),
        "os": (
            "Which operating systems do you use?",
            ["GNU/Linux", "macOS", "Windows"],
            "Pick all that apply.",
        ),
        "priorities": ("Rank your priorities.", ["Performance", "Security", "Docs &amp; manuals"]),
        "nixVersion": ("Which version of Nix do you use?",),
        "feedback": ("Anything else?",),
    },
}
DE = {
    "title": "Kleine LimeSurvey-Vorlage",
    "intro": "<p>Willkommen zur Testumfrage.</p>",
    "end": "<p>Danke fürs Mitmachen.</p>",
    "groups": [("Über dich", "Zwei Fragen zu dir."), ("Nutzung", "")],
    "q": {
        "country": ("Wo lebst du?", ["Europa", "Asien"]),
        "age": ("Wie alt bist du?", ["Unter 30", "30 oder älter"]),
        "os": (
            "Welche Betriebssysteme nutzt du?",
            ["GNU/Linux", "macOS", "Windows"],
            "Mehrfachauswahl möglich.",
        ),
        "priorities": (
            "Ordne deine Prioritäten.",
            ["Leistung", "Sicherheit", "Doku &amp; Handbücher"],
        ),
        "nixVersion": ("Welche Nix-Version nutzt du?",),
        "feedback": ("Sonst noch etwas?",),
    },
}


def main():
    """Write expected_survey.txt beside this script and report its size."""
    rows = [COLS]
    rows += [
        S("sid", "424242"),
        S("language", "en"),
        S("additional_languages", "de"),
        S("format", "G"),
        S("anonymized", "Y"),
        S("ipaddr", "N"),
        S("refurl", "N"),
        S("datestamp", "N"),
        S("savetimings", "N"),
    ]
    for lang, t in (("en", EN), ("de", DE)):
        rows += [
            SL("surveyls_title", t["title"], lang),
            SL("surveyls_welcometext", t["intro"], lang),
            SL("surveyls_endtext", t["end"], lang),
        ]
    rows += content("en", EN, ref=True)
    rows += content("de", DE, ref=False)

    out = Path(__file__).with_name("expected_survey.txt")
    with out.open("w", encoding="utf-8", newline="") as f:
        f.write("\ufeff")
        csv.writer(
            f, delimiter="\t", quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator="\n"
        ).writerows(rows)
    print(out, out.stat().st_size, "bytes", sum(1 for _ in out.open(encoding="utf-8")), "lines")


if __name__ == "__main__":
    main()
