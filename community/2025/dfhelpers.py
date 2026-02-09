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
