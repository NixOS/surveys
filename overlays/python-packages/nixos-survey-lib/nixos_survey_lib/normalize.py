import polars as pl

from .types import Question, SingleChoice, TextResponse


DEFAULT_YES_ALIASES: frozenset[str] = frozenset({"yes", "y", "yep", "yeah", "yes.", "yes!"})
DEFAULT_NO_ALIASES: frozenset[str] = frozenset({"no", "n", "nope", "nah", "no.", "no!", "no :("})


def normalize_yes_no(
    r: TextResponse,
    *,
    yes_aliases: set[str] | frozenset[str] | None = None,
    no_aliases: set[str] | frozenset[str] | None = None,
) -> SingleChoice:
    """Return a SingleChoice whose values are in {Yes, No, Other, Skipped}."""
    yes_set = set(yes_aliases) if yes_aliases is not None else set(DEFAULT_YES_ALIASES)
    no_set = set(no_aliases) if no_aliases is not None else set(DEFAULT_NO_ALIASES)

    normalized = r.values.cast(pl.Utf8).str.strip_chars().str.to_lowercase()
    out = (
        pl.when(normalized.is_null() | (normalized == ""))
        .then(pl.lit("Skipped"))
        .when(normalized.is_in(list(yes_set)))
        .then(pl.lit("Yes"))
        .when(normalized.is_in(list(no_set)))
        .then(pl.lit("No"))
        .otherwise(pl.lit("Other"))
    )

    new_q = Question(
        id=r.question.id,
        prompt=r.question.prompt,
        type="single",
        choices=["Yes", "No", "Other", "Skipped"],
        csv_columns=r.question.csv_columns,
    )
    return SingleChoice(question=new_q, values=pl.select(out).to_series())
