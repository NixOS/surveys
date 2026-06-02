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


def counts_multi(
    r: MultiChoice,
    *,
    bucket_min_percent: float | None = DEFAULT_BUCKET_MIN_PERCENT,
) -> list[Bin]:
    """For each choice, count 'Yes' responses; percent is relative to total respondents."""
    total = len(r)
    if total == 0:
        return []

    rows: list[tuple[str, int]] = []
    for choice, series in r.choice_columns.items():
        yes_count = int((series == "Yes").sum())
        rows.append((choice, yes_count))

    bins = [Bin(label=c, count=n, percent=n / total * 100.0) for c, n in rows]
    bins.sort(key=lambda b: b.percent, reverse=True)

    if bucket_min_percent is not None and bucket_min_percent > 0:
        keep = [b for b in bins if b.percent >= bucket_min_percent]
        rare = [b for b in bins if b.percent < bucket_min_percent]
        if rare:
            other_count = sum(b.count for b in rare)
            other_pct = sum(b.percent for b in rare)
            keep.append(Bin(label="Other", count=other_count, percent=other_pct))
        bins = keep

    return bins


def crosstab(
    x: SingleChoice,
    y: SingleChoice,
    *,
    normalize: Literal["global", "x", "y"] = "global",
    x_order: list[str] | None = None,
    y_order: list[str] | None = None,
    x_exclude: list[str] | None = None,
    y_exclude: list[str] | None = None,
) -> CrossTab:
    """Cross-tab two single-choice questions, normalized over global / x / y."""
    df = pl.DataFrame({"x": x.values, "y": y.values})
    if x_exclude:
        df = df.filter(~pl.col("x").is_in(list(x_exclude)))
    if y_exclude:
        df = df.filter(~pl.col("y").is_in(list(y_exclude)))

    if df.height == 0:
        return CrossTab(x_labels=[], y_labels=[], cells=[], cell_kind="rate_pct")

    def _resolve_order(arg_order: list[str] | None, series_name: str) -> list[str]:
        actual = df[series_name].unique().to_list()
        if arg_order is None:
            return df.group_by(series_name).len().sort("len", descending=True)[series_name].to_list()
        seen: set[str] = set()
        result: list[str] = []
        for v in arg_order:
            if v in actual and v not in seen:
                result.append(v)
                seen.add(v)
        for v in actual:
            if v not in seen:
                result.append(v)
        return result

    x_labels = _resolve_order(x_order, "x")
    y_labels = _resolve_order(y_order, "y")

    pairs = df.group_by(["x", "y"]).len().rename({"len": "count"})
    pair_counts: dict[tuple[str, str], int] = {
        (row["x"], row["y"]): int(row["count"]) for row in pairs.to_dicts()
    }

    total = df.height
    row_totals: dict[str, int] = {
        xl: sum(pair_counts.get((xl, yl), 0) for yl in y_labels) for xl in x_labels
    }
    col_totals: dict[str, int] = {
        yl: sum(pair_counts.get((xl, yl), 0) for xl in x_labels) for yl in y_labels
    }

    cells: list[list[float]] = []
    for xl in x_labels:
        row: list[float] = []
        for yl in y_labels:
            c = pair_counts.get((xl, yl), 0)
            if normalize == "global":
                pct = c / total * 100.0
            elif normalize == "x":
                rt = row_totals[xl]
                pct = (c / rt * 100.0) if rt > 0 else 0.0
            else:
                ct_v = col_totals[yl]
                pct = (c / ct_v * 100.0) if ct_v > 0 else 0.0
            row.append(pct)
        cells.append(row)

    return CrossTab(x_labels=x_labels, y_labels=y_labels, cells=cells, cell_kind="rate_pct")
