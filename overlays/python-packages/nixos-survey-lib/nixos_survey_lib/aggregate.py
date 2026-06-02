from typing import Literal

import polars as pl

from .types import Bin, CrossTab, MultiChoice, Ranked, Ranking, SingleChoice


DEFAULT_BUCKET_MIN_PERCENT: float = 0.5


def counts_single(
    r: SingleChoice,
    *,
    order: list[str] | None = None,
    exclude: list[str] | None = None,
    bucket_min_percent: float | None = DEFAULT_BUCKET_MIN_PERCENT,
) -> list[Bin]:
    """Count distinct values; return ordered bins with count and percent."""
    excluded = set(exclude or [])
    series = r.values
    if excluded:
        series = series.filter(~series.is_in(list(excluded)))

    total = len(series)
    if total == 0:
        return []

    counts_df = (
        series.to_frame("response")
        .group_by("response")
        .len()
        .rename({"len": "count"})
    )

    if bucket_min_percent is not None and bucket_min_percent > 0:
        counts_df = counts_df.with_columns(
            (pl.col("count") / pl.lit(float(total)) * 100.0).alias("pct")
        )
        rare = counts_df.filter(pl.col("pct") < bucket_min_percent)["response"].to_list()
        if rare:
            rare_count = counts_df.filter(pl.col("response").is_in(rare))["count"].sum()
            counts_df = counts_df.filter(~pl.col("response").is_in(rare))
            other_row = pl.DataFrame({"response": ["Other"], "count": pl.Series([int(rare_count)], dtype=pl.UInt32)})
            counts_df = pl.concat([counts_df.select(["response", "count"]), other_row])
        else:
            counts_df = counts_df.select(["response", "count"])

    if order is not None:
        rank = {v: i for i, v in enumerate(order)}
        counts_df = counts_df.with_columns(
            pl.col("response").map_elements(
                lambda v: rank.get(v, len(order)),
                return_dtype=pl.Int64,
            ).alias("_rank")
        )
        counts_df = counts_df.sort("_rank").drop("_rank")
    else:
        counts_df = counts_df.sort("count", descending=True)

    rows = counts_df.to_dicts()
    return [
        Bin(label=row["response"], count=int(row["count"]), percent=row["count"] / total * 100.0)
        for row in rows
    ]
