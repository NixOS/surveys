"""Survey definition: a TOML structure file plus one TOML text file per
language. The file layout is described in community/README.md; every rule
is documented on the function that enforces it.

Only the standard library is imported here; types.py imports from this
module, so importing anything from the package would create a cycle.
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, TypeVar

QuestionType = Literal["single", "multiple", "ranking", "text"]
Mandatory = Literal["off", "soft", "on"]
Display = Literal["radio", "dropdown"]
TextSize = Literal["short", "long"]

QUESTION_TYPES: tuple[QuestionType, ...] = ("single", "multiple", "ranking", "text")
MANDATORY_VALUES: tuple[Mandatory, ...] = ("off", "soft", "on")
DISPLAY_VALUES: tuple[Display, ...] = ("radio", "dropdown")
SIZE_VALUES: tuple[TextSize, ...] = ("short", "long")

# Question ids become LimeSurvey question codes: a letter, then letters and
# digits, at most 20 characters (Question model, rules()).
ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]{0,19}$")
# Choice keys only link texts across language files; LimeSurvey never sees them.
CHOICE_KEY_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")
# LimeSurvey language codes: "en", "pt-BR", "zh-Hant-TW", "es-AR-informal".
LANGUAGE_RE = re.compile(r"^[a-z]{2,3}(-[A-Za-z]+)*$")
# Words LimeSurvey refuses as question codes.
RESERVED_IDS = frozenset(
    w.lower()
    for w in ("LANG", "SID", "SAVEDID", "TOKEN", "QID", "GID", "SGQ", "self", "that", "this")
)
PRIVACY_KEYS = ("anonymized", "save_ip_address", "save_referrer", "date_stamp", "save_timings")

_SURVEY_KEYS = ("id", "language", "languages", "privacy")
_GROUP_KEYS = ("id", "questions")
_QUESTION_KEYS = (
    "id",
    "type",
    "mandatory",
    "choices",
    "other",
    "display",
    "alphasort",
    "max_answers",
    "size",
)
_CHOICE_TYPES = ("single", "multiple", "ranking")


class SurveyError(ValueError):
    """Any problem loading a survey definition: missing file, TOML syntax,
    or a rule violation. Messages name the file and the id involved."""


@dataclass(frozen=True)
class Privacy:
    """The five LimeSurvey settings fixed at survey activation."""

    anonymized: bool
    save_ip_address: bool
    save_referrer: bool
    date_stamp: bool
    save_timings: bool


@dataclass(frozen=True)
class StructureQuestion:
    """A question as the structure file describes it: no text yet."""

    id: str
    type: QuestionType
    mandatory: Mandatory
    choice_keys: list[str] | None
    other: bool
    display: Display
    alphasort: bool
    max_answers: int | None
    size: TextSize


@dataclass(frozen=True)
class StructureGroup:
    """A group (one survey page) as the structure file describes it."""

    id: str
    questions: list[StructureQuestion]


@dataclass(frozen=True)
class Structure:
    """The parsed structure file. Text files are validated against it."""

    id: int
    language: str
    languages: list[str]
    privacy: Privacy
    groups: list[StructureGroup]

    @property
    def questions(self) -> list[StructureQuestion]:
        """All questions in document order, across groups."""
        return [q for g in self.groups for q in g.questions]


# --- resolved model ----------------------------------------------------------
#
# Downstream code reads reference-language text from these dataclasses. The
# other languages live in Survey.texts and are only used by the converter.


@dataclass(frozen=True)
class Question:
    """A question with its reference-language text. Every field after
    `choices` has a default so callers that only know the original five
    fields (id, prompt, type, choices, csv_columns) keep working."""

    id: str
    type: QuestionType
    prompt: str
    choices: list[str] | None
    help: str | None = None
    mandatory: Mandatory = "off"
    other: bool = False
    display: Display = "radio"
    alphasort: bool = False
    max_answers: int | None = None
    size: TextSize = "long"
    choice_keys: list[str] | None = None
    csv_columns: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Group:
    """A group with its reference-language title and optional description."""

    id: str
    title: str
    description: str | None
    questions: list[Question]


@dataclass(frozen=True)
class QuestionText:
    """One language's text for one question. ``choices`` follows the
    structure file's key order, never the text file's."""

    prompt: str
    help: str | None
    choices: list[str] | None


@dataclass(frozen=True)
class GroupText:
    """One language's text for one group."""

    title: str
    description: str | None


@dataclass(frozen=True)
class LanguageTexts:
    """Everything one text file provides, keyed by group and question id."""

    language: str
    title: str
    intro: str
    end: str | None
    groups: dict[str, GroupText]
    questions: dict[str, QuestionText]


@dataclass(frozen=True)
class Survey:
    """The fully loaded survey. ``title``, ``intro``, ``end`` and the text on
    ``groups`` are exactly ``texts[language]``; ``texts`` holds every
    language, reference included, for the LimeSurvey converter."""

    id: int
    language: str
    languages: list[str]
    privacy: Privacy
    groups: list[Group]
    title: str
    intro: str
    end: str | None
    texts: dict[str, LanguageTexts]

    @property
    def questions(self) -> list[Question]:
        """All questions in document order, across groups."""
        return [q for g in self.groups for q in g.questions]


_TEXT_SURVEY_KEYS = ("title", "intro", "end")
_TEXT_GROUP_KEYS = ("title", "description")
_TEXT_QUESTION_KEYS = ("prompt", "help", "choices")


def _text(value: Any, where: str) -> str:
    """Validate a text value: a non-empty string that does not both start
    and end with a double quote. LimeSurvey's importer strips one layer of
    quotes from such cells (an Excel workaround), so ``"Other"`` would
    arrive as ``Other``.

    Text values are stripped of leading and trailing whitespace so that a
    multi-line TOML string does not carry a trailing newline into a prompt,
    and from there into the results JSON.
    """
    s = _as_str(value, where).strip()
    if not s:
        raise SurveyError(f"{where}: must not be empty")
    if len(s) >= 2 and s.startswith('"') and s.endswith('"'):
        raise SurveyError(
            f"{where}: must not both start and end with a double quote; "
            "LimeSurvey's importer strips them"
        )
    return s


def _optional_text(tbl: dict[str, Any], key: str, where: str) -> str | None:
    """A text value that may be absent. Present means the key exists; an
    empty string is an error, never an absence."""
    return _text(tbl[key], f"{where}: {key}") if key in tbl else None


def text_file_path(structure_path: Path, language: str) -> Path:
    """`survey.toml` + `de` -> `survey.de.toml`, in the same directory."""
    structure_path = Path(structure_path)
    return structure_path.with_name(f"{structure_path.stem}.{language}.toml")


def load_texts(path: Path, language: str, structure: Structure) -> LanguageTexts:
    """Read one language's text file and check it against the structure:
    one table per group and question id, exactly the listed choice keys,
    nothing extra."""
    path = Path(path)
    doc = _read_toml(path)
    name = path.name
    _check_keys(doc, ("survey", "groups", "questions"), name)

    swhere = f"{name}: [survey]"
    survey = _as_table(_require(doc, "survey", name), swhere)
    _check_keys(survey, _TEXT_SURVEY_KEYS, swhere)
    title = _text(_require(survey, "title", swhere), f"{swhere}: title")
    intro = _text(_require(survey, "intro", swhere), f"{swhere}: intro")
    end = _optional_text(survey, "end", swhere)

    gwhere = f"{name}: [groups]"
    groups_tbl = _as_table(_require(doc, "groups", name), gwhere)
    _check_keys(groups_tbl, tuple(g.id for g in structure.groups), gwhere)
    groups: dict[str, GroupText] = {}
    for g in structure.groups:
        where = f"{name}: [groups.{g.id}]"
        tbl = _as_table(_require(groups_tbl, g.id, gwhere), where)
        _check_keys(tbl, _TEXT_GROUP_KEYS, where)
        groups[g.id] = GroupText(
            title=_text(_require(tbl, "title", where), f"{where}: title"),
            description=_optional_text(tbl, "description", where),
        )

    qwhere = f"{name}: [questions]"
    questions_tbl = _as_table(_require(doc, "questions", name), qwhere)
    _check_keys(questions_tbl, tuple(q.id for q in structure.questions), qwhere)
    questions: dict[str, QuestionText] = {}
    for q in structure.questions:
        where = f"{name}: [questions.{q.id}]"
        tbl = _as_table(_require(questions_tbl, q.id, qwhere), where)
        _check_keys(tbl, _TEXT_QUESTION_KEYS, where)
        prompt = _text(_require(tbl, "prompt", where), f"{where}: prompt")
        help_text = _optional_text(tbl, "help", where)
        choices: list[str] | None = None
        if q.choice_keys is not None:
            cwhere = f"{where}: choices"
            ctbl = _as_table(_require(tbl, "choices", where), cwhere)
            _check_keys(ctbl, tuple(q.choice_keys), cwhere)
            choices = [_text(_require(ctbl, k, cwhere), f"{cwhere}.{k}") for k in q.choice_keys]
        elif "choices" in tbl:
            raise SurveyError(f"{where}: choices is not allowed on a text question")
        questions[q.id] = QuestionText(prompt=prompt, help=help_text, choices=choices)

    return LanguageTexts(
        language=language,
        title=title,
        intro=intro,
        end=end,
        groups=groups,
        questions=questions,
    )


def _check_optional_text_matches(ref: LanguageTexts, other: LanguageTexts, name: str) -> None:
    """Optional text is present in every language or in none. The reference
    language is the yardstick; ``name`` is the other file, for the message."""

    def mismatch(what: str) -> None:
        """Raise for one optional field that differs in presence."""
        raise SurveyError(
            f"{name}: {what} must be present in every language file or in none; "
            f"reference language '{ref.language}' differs"
        )

    if (ref.end is None) != (other.end is None):
        mismatch("[survey] end")
    for gid, g in ref.groups.items():
        if (g.description is None) != (other.groups[gid].description is None):
            mismatch(f"[groups.{gid}] description")
    for qid, q in ref.questions.items():
        if (q.help is None) != (other.questions[qid].help is None):
            mismatch(f"[questions.{qid}] help")


def _resolve_question(q: StructureQuestion, t: QuestionText) -> Question:
    """Combine a structure question with its reference-language text."""
    return Question(
        id=q.id,
        type=q.type,
        prompt=t.prompt,
        choices=t.choices,
        help=t.help,
        mandatory=q.mandatory,
        other=q.other,
        display=q.display,
        alphasort=q.alphasort,
        max_answers=q.max_answers,
        size=q.size,
        choice_keys=q.choice_keys,
    )


def load_survey(path: Path) -> Survey:
    """Load the structure file at `path` and every text file beside it.

    Order of checks: structure rules, then each text file against the
    structure, then stray text files for unlisted languages, then optional
    text presence across languages. Any failure raises SurveyError.
    """
    path = Path(path)
    structure = load_structure(path)

    texts: dict[str, LanguageTexts] = {}
    for lang in structure.languages:
        texts[lang] = load_texts(text_file_path(path, lang), lang, structure)

    suffix = ".toml"
    for stray in sorted(path.parent.glob(f"{path.stem}.*{suffix}")):
        lang = stray.name[len(path.stem) + 1 : -len(suffix)]
        if lang not in structure.languages:
            raise SurveyError(
                f"{stray.name}: text file for language '{lang}', "
                f"which is not listed in {path.name} [survey] languages"
            )

    ref = texts[structure.language]
    for lang, t in texts.items():
        if lang != structure.language:
            _check_optional_text_matches(ref, t, text_file_path(path, lang).name)

    groups = [
        Group(
            id=g.id,
            title=ref.groups[g.id].title,
            description=ref.groups[g.id].description,
            questions=[_resolve_question(q, ref.questions[q.id]) for q in g.questions],
        )
        for g in structure.groups
    ]
    return Survey(
        id=structure.id,
        language=structure.language,
        languages=list(structure.languages),
        privacy=structure.privacy,
        groups=groups,
        title=ref.title,
        intro=ref.intro,
        end=ref.end,
        texts=texts,
    )


# --- generic helpers ---------------------------------------------------------
#
# tomllib types values by their TOML syntax, not by what the rules expect, so
# every value is checked here before use. Each helper raises SurveyError with
# the location string the caller built up ("survey.toml: question 'os': ...").


def _read_toml(path: Path) -> dict[str, Any]:
    """Parse a TOML file, turning a missing file or a syntax error into
    SurveyError so callers have one error type to handle."""
    try:
        with path.open("rb") as f:
            return tomllib.load(f)
    except FileNotFoundError:
        raise SurveyError(f"{path.name}: file not found ({path})") from None
    except tomllib.TOMLDecodeError as e:
        raise SurveyError(f"{path.name}: invalid TOML: {e}") from None


def _check_keys(table: dict[str, Any], allowed: tuple[str, ...], where: str) -> None:
    """Reject any key not in ``allowed``; typos must not pass silently."""
    for key in table:
        if key not in allowed:
            raise SurveyError(f"{where}: unknown key '{key}'")


def _require(table: dict[str, Any], key: str, where: str) -> Any:
    """Return ``table[key]`` or raise naming the missing key."""
    if key not in table:
        raise SurveyError(f"{where}: missing required key '{key}'")
    return table[key]


def _as_str(value: Any, where: str) -> str:
    """Type check: the value must be a TOML string."""
    if not isinstance(value, str):
        raise SurveyError(f"{where}: expected a string")
    return value


def _as_bool(value: Any, where: str) -> bool:
    """Type check: the value must be a TOML boolean, not "yes" or 1."""
    if not isinstance(value, bool):
        raise SurveyError(f"{where}: expected true or false")
    return value


def _as_int(value: Any, where: str) -> int:
    """Type check: a TOML integer. bool is excluded explicitly because it is
    a subclass of int in Python and ``id = true`` must not pass as 1."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise SurveyError(f"{where}: expected an integer")
    return value


def _as_table(value: Any, where: str) -> dict[str, Any]:
    """Type check: the value must be a TOML table."""
    if not isinstance(value, dict):
        raise SurveyError(f"{where}: expected a table")
    return value


def _as_list_of_str(value: Any, where: str) -> list[str]:
    """Type check: a TOML array whose elements are all strings."""
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise SurveyError(f"{where}: expected a list of strings")
    return value


_Choice = TypeVar("_Choice", QuestionType, Mandatory, Display, TextSize)


def _one_of(value: Any, options: tuple[_Choice, ...], where: str) -> _Choice:
    """Enum check: the value must be one of ``options``. The return type
    follows the options tuple, so callers get the literal type rather than
    a bare ``str``."""
    if value not in options:
        raise SurveyError(f"{where}: must be one of {', '.join(options)}, got {value!r}")
    return value


def _check_unique(values: list[str], where: str, what: str) -> None:
    """Reject duplicates, comparing case-insensitively. LimeSurvey's own
    uniqueness check runs on a case-insensitive database collation, so
    ``Country`` and ``country`` would collide on import."""
    seen: dict[str, str] = {}
    for v in values:
        if v.lower() in seen:
            raise SurveyError(
                f"{where}: duplicate {what} '{v}' (matches '{seen[v.lower()]}' case-insensitively)"
            )
        seen[v.lower()] = v


def _check_language_code(code: str, where: str) -> None:
    """Shape check only; LimeSurvey rejects unknown codes at import time."""
    if not LANGUAGE_RE.match(code):
        raise SurveyError(f"{where}: invalid language code '{code}'")


# --- structure file ----------------------------------------------------------


def load_structure(path: Path) -> Structure:
    """Read and validate the structure file. Text files are not touched."""
    path = Path(path)
    doc = _read_toml(path)
    name = path.name
    _check_keys(doc, ("survey", "groups"), name)

    survey = _as_table(_require(doc, "survey", name), f"{name}: [survey]")
    where = f"{name}: [survey]"
    _check_keys(survey, _SURVEY_KEYS, where)
    sid = _as_int(_require(survey, "id", where), f"{where}: id")
    if sid < 2:
        raise SurveyError(f"{where}: id must be at least 2, got {sid}")
    language = _as_str(_require(survey, "language", where), f"{where}: language")
    _check_language_code(language, f"{where}: language")
    languages = _as_list_of_str(_require(survey, "languages", where), f"{where}: languages")
    if not languages:
        raise SurveyError(f"{where}: languages must not be empty")
    for code in languages:
        _check_language_code(code, f"{where}: languages")
    _check_unique(languages, f"{where}: languages", "language")
    if language not in languages:
        raise SurveyError(f"{where}: language '{language}' is not listed in languages")

    pwhere = f"{name}: [survey.privacy]"
    privacy_tbl = _as_table(_require(survey, "privacy", where), pwhere)
    _check_keys(privacy_tbl, PRIVACY_KEYS, pwhere)
    privacy = Privacy(
        **{k: _as_bool(_require(privacy_tbl, k, pwhere), f"{pwhere}: {k}") for k in PRIVACY_KEYS}
    )

    raw_groups = doc.get("groups")
    if not isinstance(raw_groups, list) or not raw_groups:
        raise SurveyError(f"{name}: at least one [[groups]] entry is required")
    groups = [_parse_group(g, name) for g in raw_groups]
    _check_unique([g.id for g in groups], name, "group id")
    _check_unique([q.id for g in groups for q in g.questions], name, "question id")
    return Structure(id=sid, language=language, languages=languages, privacy=privacy, groups=groups)


def _parse_group(raw: Any, name: str) -> StructureGroup:
    """Validate one [[groups]] entry and its questions."""
    tbl = _as_table(raw, f"{name}: [[groups]]")
    gid = _as_str(_require(tbl, "id", f"{name}: [[groups]]"), f"{name}: [[groups]]: id")
    where = f"{name}: group '{gid}'"
    if not ID_RE.match(gid):
        raise SurveyError(f"{where}: group id must match {ID_RE.pattern}")
    _check_keys(tbl, _GROUP_KEYS, where)
    raw_questions = tbl.get("questions")
    if not isinstance(raw_questions, list) or not raw_questions:
        raise SurveyError(f"{where}: at least one [[groups.questions]] entry is required")
    return StructureGroup(
        id=gid, questions=[_parse_question(q, name, where) for q in raw_questions]
    )


def _parse_question(raw: Any, name: str, group_where: str) -> StructureQuestion:
    """Validate one [[groups.questions]] entry: id rules, type, and the
    fields each type allows (each type's allowed fields are checked below).

    ``group_where`` names the group the entry sits in, so an entry with no
    id of its own can still be located.
    """
    qwhere = f"{group_where}: [[groups.questions]]"
    tbl = _as_table(raw, qwhere)
    qid = _as_str(_require(tbl, "id", qwhere), f"{qwhere}: id")
    where = f"{name}: question '{qid}'"
    if not ID_RE.match(qid):
        raise SurveyError(
            f"{where}: id must match {ID_RE.pattern} (letter first, letters and digits, at most 20)"
        )
    if qid.lower() in RESERVED_IDS:
        raise SurveyError(f"{where}: id is a LimeSurvey reserved word")
    _check_keys(tbl, _QUESTION_KEYS, where)
    qtype = _one_of(_require(tbl, "type", where), QUESTION_TYPES, f"{where}: type")
    mandatory = _one_of(tbl.get("mandatory", "off"), MANDATORY_VALUES, f"{where}: mandatory")

    choice_keys: list[str] | None = None
    if qtype in _CHOICE_TYPES:
        choice_keys = _as_list_of_str(_require(tbl, "choices", where), f"{where}: choices")
        if not choice_keys:
            raise SurveyError(f"{where}: choices must not be empty")
        for key in choice_keys:
            if not CHOICE_KEY_RE.match(key):
                raise SurveyError(f"{where}: choice key '{key}' must match {CHOICE_KEY_RE.pattern}")
        _check_unique(choice_keys, f"{where}: choices", "choice key")
    elif "choices" in tbl:
        raise SurveyError(f"{where}: choices is not allowed on a text question")

    other = False
    if "other" in tbl:
        if qtype not in ("single", "multiple"):
            raise SurveyError(f"{where}: other is only allowed on single and multiple questions")
        other = _as_bool(tbl["other"], f"{where}: other")

    display = "radio"
    if "display" in tbl:
        if qtype != "single":
            raise SurveyError(f"{where}: display is only allowed on single questions")
        display = _one_of(tbl["display"], DISPLAY_VALUES, f"{where}: display")

    alphasort = False
    if "alphasort" in tbl:
        if qtype != "single":
            raise SurveyError(f"{where}: alphasort is only allowed on single questions")
        alphasort = _as_bool(tbl["alphasort"], f"{where}: alphasort")

    max_answers: int | None = None
    if "max_answers" in tbl:
        if qtype not in ("multiple", "ranking"):
            raise SurveyError(
                f"{where}: max_answers is only allowed on multiple and ranking questions"
            )
        max_answers = _as_int(tbl["max_answers"], f"{where}: max_answers")
        assert choice_keys is not None
        if not 1 <= max_answers <= len(choice_keys):
            raise SurveyError(
                f"{where}: max_answers must be between 1 and {len(choice_keys)}, got {max_answers}"
            )

    size = "long"
    if "size" in tbl:
        if qtype != "text":
            raise SurveyError(f"{where}: size is only allowed on text questions")
        size = _one_of(tbl["size"], SIZE_VALUES, f"{where}: size")

    return StructureQuestion(
        id=qid,
        type=qtype,
        mandatory=mandatory,
        choice_keys=choice_keys,
        other=other,
        display=display,
        alphasort=alphasort,
        max_answers=max_answers,
        size=size,
    )
