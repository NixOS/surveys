import re

import polars as pl

SEMVER_MMP_RE = (
    r"(?:^|[^0-9])((?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*))(?:$|[^0-9])"
)


def extract_first_mmp_semver_df(
    df: pl.DataFrame,
    column: str | int,
    *,
    min_percent: float | None = None,  # e.g. 1.0 means "below 1% -> Other"
    skipped_label: str = "Skipped",
    no_match_label: str = "No Match",
    rare_label: str = "Other",
) -> pl.DataFrame:
    col = df.columns[column] if isinstance(column, int) else column

    cleaned = (
        pl.col(col)
        .cast(pl.Utf8)
        .str.strip_chars()
        .replace("", None)  # empty -> null
        .fill_null(skipped_label)  # null -> "Skipped" before regex
    )

    extracted = cleaned.str.extract(SEMVER_MMP_RE, group_index=1)

    out = df.select(
        pl.when(cleaned == skipped_label)
        .then(pl.lit(skipped_label))
        .otherwise(extracted)
        .fill_null(no_match_label)
        .alias(col)
    )

    # Bucket rare versions into "Other"
    if min_percent is not None and min_percent > 0 and out.height > 0:
        total = float(out.height)
        special = [skipped_label, no_match_label, rare_label]

        counts = (
            out.group_by(col)
            .len()
            .rename({"len": "count"})
            .with_columns((pl.col("count") / pl.lit(total) * 100.0).alias("pct"))
        )

        rare_values = (
            counts.filter((pl.col("pct") < min_percent) & (~pl.col(col).is_in(special)))
            .select(col)
            .to_series()
            .to_list()
        )

        if rare_values:
            out = out.with_columns(
                pl.when(pl.col(col).is_in(rare_values))
                .then(pl.lit(rare_label))
                .otherwise(pl.col(col))
                .alias(col)
            )

    return out


def reduce_multi_choice_to_single_column(df, first, last):
    question_pat = re.match(r"^(.*?)\s*\[[^\]]+\]\s*$", df[:, first].name)
    title = question_pat.group(1)

    multi = (df[:, first:last] == "Yes").mean()
    square_pat = re.compile(r"\[([^\]]+)\]\s*$")
    multi = multi.rename(
        {
            c: square_pat.search(c).group(1) if square_pat.search(c) else c
            for c in multi.columns
        }
    )

    return (
        multi.melt(variable_name="response", value_name="len")
        .with_columns((pl.col("len") * 100).alias("len"))
        .sort("len", descending=True),
        title,
    )


def bucket_rare_categories_df(
    df: pl.DataFrame,
    column: str | int,
    *,
    min_percent: float = 0.0,  # below this => bucketed
    other_label: str = "Other",
    exclude: list[str]
    | None = None,  # labels never bucketed (e.g. ["Skipped", "No Match"])
) -> pl.DataFrame:
    """
    Returns a 1-column DataFrame where values whose percent contribution is < min_percent
    are replaced with other_label.

    - Percent contribution is computed over all rows (including nulls if present).
    - Does not modify the input df.
    """
    col = df.columns[column] if isinstance(column, int) else column
    exclude_set = set(exclude or [])
    exclude_set.add(other_label)  # don't bucket the bucket

    out = df.select(pl.col(col))
    n = out.height
    if n == 0 or min_percent <= 0:
        return out

    counts = out.group_by(col).len().rename({"len": "count"})
    counts = counts.with_columns(
        (pl.col("count") / pl.lit(float(n)) * 100.0).alias("pct")
    )

    rare_values = (
        counts.filter(
            (pl.col("pct") < min_percent) & (~pl.col(col).is_in(list(exclude_set)))
        )
        .select(col)
        .to_series()
        .to_list()
    )

    if not rare_values:
        return out

    return out.with_columns(
        pl.when(pl.col(col).is_in(rare_values))
        .then(pl.lit(other_label))
        .otherwise(pl.col(col))
        .alias(col)
    )


import re as _re_token
from collections import Counter as _Counter

DEFAULT_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "by", "for", "from",
    "has", "have", "had", "he", "her", "him", "his", "i", "in", "is", "it",
    "its", "me", "my", "of", "on", "or", "our", "she", "that", "the", "to",
    "us", "was", "we", "were", "will", "with", "you", "your", "this",
    "these", "those", "but", "not", "if", "so", "do", "does", "did", "can",
    "could", "should", "would", "than", "then", "there", "here", "when",
    "where", "what", "which", "who", "how", "why", "all", "any", "some",
    "yes", "no", "just", "also", "very", "much", "more", "most", "less",
    "only", "even", "still", "yet", "out", "up", "down", "over", "under",
    "about", "into", "through", "after", "before", "while", "during",
    "because", "though", "although", "however", "thus", "hence", "therefore",
    "such", "like", "well", "really", "actually", "perhaps", "maybe",
    "thats", "im", "ive", "id", "youre", "youd", "youve",
    "dont", "doesnt", "didnt", "isnt", "arent", "wasnt", "werent",
    "cant", "couldnt", "wouldnt", "shouldnt",
    # Nix-specific (dominate every chart otherwise)
    "nix", "nixos", "nixpkgs",
}


def tokenize_text_column(
    df: pl.DataFrame,
    col: int | str,
    *,
    min_token_len: int = 2,
    extra_stopwords: list[str] | None = None,
) -> dict[str, int]:
    """Lowercase, tokenize on non-alphanumeric, drop short tokens and stopwords,
    return token -> count."""
    col_name = df.columns[col] if isinstance(col, int) else col
    stopwords = set(DEFAULT_STOPWORDS)
    if extra_stopwords:
        stopwords.update(s.lower() for s in extra_stopwords)

    counter: _Counter[str] = _Counter()
    for raw in df[col_name].cast(pl.Utf8).to_list():
        if raw is None:
            continue
        text = raw.lower()
        for tok in _re_token.findall(r"[a-z0-9]+", text):
            if len(tok) < min_token_len:
                continue
            if tok in stopwords:
                continue
            counter[tok] += 1
    return dict(counter)


DEFAULT_YES_ALIASES = {"yes", "y", "yep", "yeah", "yes.", "yes!"}
DEFAULT_NO_ALIASES = {"no", "n", "nope", "nah", "no.", "no!", "no :("}


def normalize_yes_no_column(
    df: pl.DataFrame,
    col: int | str,
    *,
    yes_aliases: set[str] | None = None,
    no_aliases: set[str] | None = None,
) -> pl.DataFrame:
    """Return a 1-column DataFrame where the chosen column has been
    normalized into one of {"Yes", "No", "Other", "Skipped"} based on
    case-insensitive exact match against the alias sets. Empty/whitespace
    -> "Skipped"; values not matching any alias -> "Other"."""
    col_name = df.columns[col] if isinstance(col, int) else col
    yes_set = set(yes_aliases) if yes_aliases is not None else set(DEFAULT_YES_ALIASES)
    no_set = set(no_aliases) if no_aliases is not None else set(DEFAULT_NO_ALIASES)

    normalized = (
        pl.col(col_name)
        .cast(pl.Utf8)
        .str.strip_chars()
        .str.to_lowercase()
    )

    return df.select(
        pl.when(normalized.is_null() | (normalized == ""))
        .then(pl.lit("Skipped"))
        .when(normalized.is_in(list(yes_set)))
        .then(pl.lit("Yes"))
        .when(normalized.is_in(list(no_set)))
        .then(pl.lit("No"))
        .otherwise(pl.lit("Other"))
        .alias(col_name)
    )
