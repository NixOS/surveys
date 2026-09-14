"""Turn a Survey into LimeSurvey's tab-separated survey structure (.txt).

Row classes: S (survey setting), SL (per-language survey text), G (group),
Q (question), SQ (subquestion, the checkboxes of a multiple-choice
question), A (answer, the options of a single-choice or ranking question).
Nesting is by order: a Q belongs to the G above it, SQ/A rows to the Q
above them. Multi-language surveys repeat the whole G/Q/SQ/A block once per
language, reference language first; the importer links the copies by group
number, question code, and generated choice codes.

Read against LimeSurvey 6.15.14: application/helpers/admin/import_helper.php
(TSVImportSurvey) and application/helpers/export_helper.php (tsvSurveyExport).
"""

from __future__ import annotations

import csv
import io
import re

from .schema import LanguageTexts, Question, Survey

BOM = "\ufeff"

# LimeSurvey's exporter writes these sixteen columns in this order; the
# header here ends with the two question attributes this converter uses. The
# importer reads every non-empty cell whose column is not in its skip list
# (class, type/scale, name, text, validation, relevance, help, language,
# mandatory, other, same_default, same_script, default) as a question
# attribute. That includes id, related_id and encrypted, which is why those
# cells stay empty.
COLUMNS = (
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
    "answer_order",
)

_WS = re.compile(r"\s+")
_NEWLINES = re.compile(r"[\r\n]+")
_MANDATORY = {"off": "N", "soft": "S", "on": "Y"}


def plain(text: str) -> str:
    """Plain text cell: one line, passed through unescaped.

    LimeSurvey encodes these values itself when it renders them, so escaping
    here is applied twice: "Antigua & Barbuda" reaches the browser as
    "Antigua &amp;amp; Barbuda" and the respondent reads "Antigua &amp;
    Barbuda". The 2025 survey has shipped "Latin America &amp; the Caribbean"
    in its country question for this reason.

    Quotes are left alone; the csv layer handles them.
    """
    return _WS.sub(" ", text).strip()


def html_text(text: str) -> str:
    """HTML cell (intro, end): passed through, made one-line."""
    return _NEWLINES.sub(" ", text)


def type_letter(q: Question) -> str:
    """LimeSurvey's one-letter question type for a TOML question type."""
    if q.type == "single":
        return "L" if q.display == "radio" else "!"
    if q.type == "multiple":
        return "M"
    if q.type == "ranking":
        return "R"
    return "T" if q.size == "long" else "S"


def _yn(flag: bool) -> str:
    """LimeSurvey stores booleans as Y/N strings."""
    return "Y" if flag else "N"


def _row(**cells: str) -> list[str]:
    """Build one row; keyword names are column names with `/` written as `_`
    and `class` as `cls`. Columns not named stay empty, which makes the
    importer apply its own defaults."""
    mapping = {"cls": "class", "type_scale": "type/scale"}
    named = {mapping.get(k, k): v for k, v in cells.items()}
    assert set(named) <= set(COLUMNS), sorted(set(named) - set(COLUMNS))
    return [named.get(c, "") for c in COLUMNS]


def _language_order(survey: Survey) -> list[str]:
    """Reference language first, then the rest in the structure's order.
    Both the SL block and the content blocks follow this order."""
    return [survey.language] + [lang for lang in survey.languages if lang != survey.language]


def _settings_rows(survey: Survey) -> list[list[str]]:
    """S rows: the survey id, languages, page format and privacy flags.
    Everything not written here gets LimeSurvey's default on import."""
    p = survey.privacy
    rows = [
        _row(cls="S", name="sid", text=str(survey.id)),
        _row(cls="S", name="language", text=survey.language),
    ]
    additional = _language_order(survey)[1:]
    if additional:
        rows.append(_row(cls="S", name="additional_languages", text=" ".join(additional)))
    if survey.template is not None:
        # The theme. Pinning it here means the survey looks the same whatever
        # the server's default is, which is the difference between a readable
        # instrument and one nobody can fix without admin access.
        rows.append(_row(cls="S", name="template", text=survey.template))
    rows += [
        _row(cls="S", name="format", text="G"),  # one group per page
        _row(cls="S", name="anonymized", text=_yn(p.anonymized)),
        _row(cls="S", name="ipaddr", text=_yn(p.save_ip_address)),
        _row(cls="S", name="refurl", text=_yn(p.save_referrer)),
        _row(cls="S", name="datestamp", text=_yn(p.date_stamp)),
        _row(cls="S", name="savetimings", text=_yn(p.save_timings)),
    ]
    return rows


def _language_settings_rows(t: LanguageTexts) -> list[list[str]]:
    """SL rows for one language: title, welcome text, and end text if any."""
    rows = [
        _row(cls="SL", name="surveyls_title", text=plain(t.title), language=t.language),
        _row(cls="SL", name="surveyls_welcometext", text=html_text(t.intro), language=t.language),
    ]
    if t.end is not None:
        rows.append(
            _row(cls="SL", name="surveyls_endtext", text=html_text(t.end), language=t.language)
        )
    return rows


def _content_rows(survey: Survey, t: LanguageTexts, *, is_reference: bool) -> list[list[str]]:
    """The G/Q/SQ/A block for one language.

    Group number and choice codes are positional so the importer can line
    up translations. Attributes (max_answers, answer_order) go on the
    reference-language row only; the importer would otherwise store them once
    per language.

    ``answer_order`` is LimeSurvey 6's name for alphabetical answer sorting.
    It supersedes the legacy ``alphasort`` attribute, takes precedence over it
    in Question::shouldOrderAnswersAlphabetically, and is what the admin UI
    writes when anyone saves the question, so emitting the legacy name would
    produce a setting that works until someone looks at it.
    """
    rows: list[list[str]] = []
    for number, group in enumerate(survey.groups, start=1):
        gt = t.groups[group.id]
        rows.append(
            _row(
                cls="G",
                type_scale=str(number),
                name=plain(gt.title),
                text=plain(gt.description) if gt.description is not None else "",
                language=t.language,
            )
        )
        for q in group.questions:
            qt = t.questions[q.id]
            rows.append(
                _row(
                    cls="Q",
                    type_scale=type_letter(q),
                    name=q.id,
                    relevance="1",
                    text=plain(qt.prompt),
                    help=plain(qt.help) if qt.help is not None else "",
                    language=t.language,
                    mandatory=_MANDATORY[q.mandatory],
                    other=_yn(q.other),
                    max_answers=str(q.max_answers)
                    if is_reference and q.max_answers is not None
                    else "",
                    answer_order="alphabetical" if is_reference and q.alphasort else "",
                )
            )
            if qt.choices is None:
                continue
            if q.type == "multiple":
                for i, choice in enumerate(qt.choices, start=1):
                    rows.append(
                        _row(cls="SQ", name=f"SQ{i:03d}", text=plain(choice), language=t.language)
                    )
            else:
                for i, choice in enumerate(qt.choices, start=1):
                    rows.append(
                        _row(
                            cls="A",
                            type_scale="0",
                            name=f"A{i}",
                            text=plain(choice),
                            language=t.language,
                        )
                    )
    return rows


def to_tsv(survey: Survey) -> str:
    """The import file as text, starting with a byte-order mark. Write it
    with encoding="utf-8" and newline=""."""
    rows: list[list[str]] = [list(COLUMNS)]
    rows += _settings_rows(survey)
    order = _language_order(survey)
    for lang in order:
        rows += _language_settings_rows(survey.texts[lang])
    for lang in order:
        rows += _content_rows(survey, survey.texts[lang], is_reference=(lang == survey.language))
    buf = io.StringIO()
    writer = csv.writer(
        buf, delimiter="\t", quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator="\n"
    )
    writer.writerows(rows)
    return BOM + buf.getvalue()
