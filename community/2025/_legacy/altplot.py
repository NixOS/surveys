import textwrap

import altair as alt
import pandas as pd
import panel as pn
import polars as pl
from dfhelpers import (
    bucket_rare_categories_df,
    reduce_multi_choice_to_single_column,
)


def pretty_bar_chart(pdf, title, max_items=25, height_step=18):
    pdf = pdf.copy()

    # Optional: keep top N and roll remainder into "Other"
    if len(pdf) > max_items:
        top = pdf.iloc[:max_items].copy()
        other = pdf.iloc[max_items:]["len"].sum()
        top.loc[len(top)] = {"response": "Other", "len": int(other)}
        pdf = top

    total = float(pdf["len"].sum()) if len(pdf) else 0.0
    if total > 0:
        pdf["pct"] = (pdf["len"] / total) * 100.0
    else:
        pdf["pct"] = 0.0
    pdf["pct_label"] = pdf["pct"].map(lambda v: f"{v:.1f}%")

    height = max(240, len(pdf) * height_step)

    base = alt.Chart(pdf).encode(
        y=alt.Y(
            "response:N",
            sort="-x",
            title=None,
            axis=alt.Axis(labelLimit=320, labelFontSize=12, ticks=False),
        ),
        x=alt.X(
            "len:Q",
            title=None,
            axis=alt.Axis(labelFontSize=12, ticks=False, grid=True),
        ),
        tooltip=[
            alt.Tooltip("response:N", title="Response"),
            alt.Tooltip("len:Q", title="Count"),
            alt.Tooltip("pct:Q", title="Percent", format=".1f"),
        ],
    )

    bars = base.mark_bar(cornerRadius=3)

    labels = base.mark_text(
        align="left",
        baseline="middle",
        dx=4,
        fontSize=12,
    ).encode(text=alt.Text("pct_label:N"))

    return (
        (bars + labels)
        .properties(
            title=alt.TitleParams(
                text=title,
                fontSize=18,
                anchor="start",
                subtitle=["Counts (bars) with percent labels"],
                subtitleFontSize=12,
            ),
            height=height,
        )
        .configure_view(strokeWidth=0)
        .configure_axis(domain=False, gridOpacity=0.35)
        .configure_title(offset=10)
    )


def so_style_bar_chart(
    pdf,
    title: str,
    *,
    normalize: bool = True,
    label_width: int = 240,
    bar_width: int = 460,
    step: int = 24,  # controls row height => constant bar thickness
    bar_size: int = 16,  # actual bar thickness
    gap: int = 0,  # gap between label column and bars
    label_order: list[str] | None = None,
    label_fade_px: int = 48,  # width of the fade region
    label_fade_steps: int = 4,  # smoothness of fade
    label_bg: str = "#ffffff",  # match your card background
    label_format=lambda v: f"{v:.1f}%",
    sort_ascending: bool = False,
):
    pdf = pdf.copy()

    # Default: order by count (descending = SO default; ascending = ranking by mean)
    if label_order is None:
        pdf = pdf.sort_values("len", ascending=sort_ascending)
        order = pdf["response"].tolist()
    else:
        present = set(pdf["response"].tolist())

        # keep user order (deduped) but only for labels present in the data
        seen = set()
        user_part = []
        for s in label_order:
            if s in present and s not in seen:
                user_part.append(s)
                seen.add(s)

        # append anything not specified, by count desc
        rest = pdf.sort_values("len", ascending=False)["response"].tolist()
        rest = [s for s in rest if s not in seen]
        order = user_part + rest

        # Optional: sort the dataframe to match the final display order (nice for debugging)
        rank = {s: i for i, s in enumerate(order)}
        pdf["_order"] = pdf["response"].map(rank)
        pdf = pdf.sort_values("_order").drop(columns=["_order"])

    if normalize:
        total = float(pdf["len"].sum()) if len(pdf) else 0.0
        pdf["pct"] = (pdf["len"] / total * 100.0) if total > 0 else 0.0
    else:
        # len is already the value you want to display
        pdf["pct"] = pdf["len"]

    pdf["pct_label"] = pdf["pct"].map(label_format)
    max_len = float(pdf["len"].max()) if len(pdf) else 1.0

    # Shared y encoding with dotted horizontal separators between bars
    y_grid = alt.Y(
        "response:N",
        sort=order,
        title=None,
        axis=alt.Axis(
            title=None,
            labels=False,
            ticks=False,
            domain=False,
            grid=True,
            tickBand="extent",
            gridDash=[2, 4],  # dotted
            gridOpacity=1.0,
        ),
    )

    labels_text = (
        alt.Chart(pdf)
        .mark_text(
            align="left",
            baseline="middle",
            fontSize=12,
            clip=True,
            limit=label_width + gap,
        )
        .encode(
            y=y_grid,
            x=alt.value(0),  # pin to left edge
            text="response:N",
        )
        .properties(width=label_width + gap, height=alt.Step(step))
    )

    fade_layers = []
    if label_fade_px and label_fade_px > 0:
        steps = label_fade_steps
        start = (label_width + gap) - label_fade_px
        w = label_fade_px / max(1, steps)

        for i in range(steps):
            x0 = start + i * w
            x1 = start + (i + 1) * w
            opacity = (i + 1) / steps

            fade_layers.append(
                alt.Chart(pdf)
                .mark_bar(
                    orient="horizontal",
                    color=label_bg,
                    opacity=opacity,
                    size=bar_size,
                )
                .encode(
                    y=y_grid,
                    x=alt.value(x0),
                    x2=alt.value(x1),
                )
                .properties(width=label_width + gap, height=alt.Step(step))
            )

    labels = alt.layer(labels_text, *fade_layers).properties(
        width=label_width + gap, height=alt.Step(step)
    )

    base = alt.Chart(pdf).encode(
        y=y_grid,
        x=alt.X(
            "len:Q",
            axis=None,
            scale=alt.Scale(domain=(0, max_len * 1.12)),
        ),
        tooltip=[
            alt.Tooltip("response:N", title="Response"),
            alt.Tooltip("len:Q", title="Count"),
            alt.Tooltip("pct:Q", title="Percent", format=".1f"),
        ],
    )

    bars = base.mark_bar(size=bar_size, cornerRadius=bar_size // 4)
    pct = base.mark_text(align="left", baseline="middle", dx=6, fontSize=12).encode(
        text="pct_label:N"
    )

    bars_block = (bars + pct).properties(width=bar_width, height=alt.Step(step))

    return (
        alt.hconcat(labels, bars_block, spacing=0)  # no empty gap between charts
        .resolve_scale(y="shared")
        .properties(
            title=alt.TitleParams(
                text=wrap_title(title),
                anchor="start",
                fontSize=18,
                offset=10,
            )
        )
        .configure_view(strokeWidth=0)
    )


def wrap_title(s: str, width: int = 72) -> list[str]:
    return textwrap.wrap(s, width=width, break_long_words=False)


def make_simple_bar_chart_pane(df, column, label_order=None):
    col_name = df.columns[column]
    counts = (
        df.select(
            pl.col(col_name)
            .cast(pl.Utf8)
            .str.strip_chars()
            .replace("", None)
            .fill_null("Skipped")
            .alias("response")
        )
        .with_columns(
            pl.when(pl.col("response").str.len_chars() > 60)
            .then(pl.col("response").str.slice(0, 57) + "…")
            .otherwise(pl.col("response"))
            .alias("response_short")
        )
        .group_by(["response", "response_short"])
        .len()
        .sort("len", descending=True)
    )

    pdf = counts.to_pandas()

    chart = so_style_bar_chart(pdf, title=col_name, label_order=label_order)
    altair_pane = pn.pane.Vega(chart, sizing_mode="stretch_width")

    return altair_pane


def make_multi_bar_chart_pane(df, first, last, min_percent=0.0, title=None):
    reduced, auto_title = reduce_multi_choice_to_single_column(df, first, last)

    if min_percent > 0:
        reduced = bucket_rare_categories_df(reduced, 0, min_percent=min_percent)

    pdf = reduced.to_pandas()

    chart = so_style_bar_chart(pdf, title=title or auto_title, normalize=False, label_order=None)
    altair_pane = pn.pane.Vega(chart, sizing_mode="stretch_width")

    return altair_pane


def _merge_order(
    user_order: list[str] | None, actual: list[str], fallback: list[str]
) -> list[str]:
    """Keep user_order (filtered to existing, deduped) then append remaining via fallback order."""
    if user_order is None:
        return fallback
    present = set(actual)
    seen: set[str] = set()
    out: list[str] = []
    for s in user_order:
        if s in present and s not in seen:
            out.append(s)
            seen.add(s)
    out.extend([s for s in fallback if s not in seen])
    return out


def heatmap_from_col_indices(
    df: pl.DataFrame,
    x_idx: int,
    y_idx: int,
    *,
    # ordering
    x_order: list[str] | None = None,
    y_order: list[str] | None = None,
    # filtering
    x_exclude: list[str] | None = None,
    y_exclude: list[str] | None = None,
    fill_empty_as: str = "Skipped",
    complete_grid: bool = True,
    # value + normalization
    value: str = "count",  # "count" or "percent"
    normalize: str = "global",  # "global" | "x" | "y" (only if value="percent")
    # sizing
    width: int | str = "container",
    height: int = 400,
    # formatting
    percent_decimals: int = 1,
    # misc
    title: str | None = None,
):
    if value not in {"count", "percent"}:
        raise ValueError("value must be 'count' or 'percent'")
    if normalize not in {"global", "x", "y"}:
        raise ValueError("normalize must be 'global', 'x', or 'y'")

    x_col = df.columns[x_idx]
    y_col = df.columns[y_idx]
    x_ex = set(x_exclude or [])
    y_ex = set(y_exclude or [])

    # Clean
    cleaned = df.select(
        pl.col(x_col)
        .cast(pl.Utf8)
        .str.strip_chars()
        .replace("", None)
        .fill_null(fill_empty_as)
        .alias(x_col),
        pl.col(y_col)
        .cast(pl.Utf8)
        .str.strip_chars()
        .replace("", None)
        .fill_null(fill_empty_as)
        .alias(y_col),
    )
    if x_ex:
        cleaned = cleaned.filter(~pl.col(x_col).is_in(list(x_ex)))
    if y_ex:
        cleaned = cleaned.filter(~pl.col(y_col).is_in(list(y_ex)))

    # Count pairs
    pairs = cleaned.group_by([x_col, y_col]).len().rename({"len": "count"})

    # Axis totals for default ordering (always based on counts)
    x_fallback = (
        pairs.group_by(x_col)
        .agg(pl.sum("count").alias("total"))
        .sort("total", descending=True)[x_col]
        .to_list()
    )
    y_fallback = (
        pairs.group_by(y_col)
        .agg(pl.sum("count").alias("total"))
        .sort("total", descending=True)[y_col]
        .to_list()
    )

    actual_x = cleaned.select(pl.col(x_col)).unique()[x_col].to_list()
    actual_y = cleaned.select(pl.col(y_col)).unique()[y_col].to_list()

    x_sort = _merge_order(x_order, actual_x, x_fallback)
    y_sort = _merge_order(y_order, actual_y, y_fallback)

    # Complete grid with zeros
    if complete_grid:
        grid = pl.DataFrame({x_col: x_sort}).join(
            pl.DataFrame({y_col: y_sort}), how="cross"
        )
        pairs = grid.join(pairs, on=[x_col, y_col], how="left").with_columns(
            pl.col("count").fill_null(0)
        )

    # Add percent column if requested
    if value == "percent":
        if normalize == "global":
            total = pairs.select(pl.sum("count").alias("_total")).to_series()[0]
            total = float(total or 0.0)

            pairs = pairs.with_columns(
                pl.when(pl.lit(total) > 0)
                .then(pl.col("count") / pl.lit(total) * 100)
                .otherwise(0.0)
                .alias("percent")
            )

        elif normalize == "x":
            denom = pl.sum("count").over(x_col)  # note: over(x_col), not over([x_col])
            pairs = pairs.with_columns(
                pl.when(denom > 0)
                .then(pl.col("count") / denom * 100)
                .otherwise(0.0)
                .alias("percent")
            )

        else:  # normalize == "y"
            denom = pl.sum("count").over(y_col)
            pairs = pairs.with_columns(
                pl.when(denom > 0)
                .then(pl.col("count") / denom * 100)
                .otherwise(0.0)
                .alias("percent")
            )

    pdf = pairs.to_pandas()

    if value == "count":
        color_field = "count:Q"
        legend_title = "Count"
        tooltip = [
            alt.Tooltip(f"{x_col}:N", title=x_col),
            alt.Tooltip(f"{y_col}:N", title=y_col),
            alt.Tooltip("count:Q", title="Count"),
        ]
    else:
        color_field = "percent:Q"
        legend_title = f"Percent ({normalize})"
        tooltip = [
            alt.Tooltip(f"{x_col}:N", title=x_col),
            alt.Tooltip(f"{y_col}:N", title=y_col),
            alt.Tooltip("percent:Q", title="Percent", format=f".{percent_decimals}f"),
            alt.Tooltip("count:Q", title="Count"),
        ]

    chart = (
        alt.Chart(pdf)
        .mark_rect()
        .encode(
            x=alt.X(f"{x_col}:N", sort=x_sort, title=x_col),
            y=alt.Y(f"{y_col}:N", sort=y_sort, title=y_col),
            color=alt.Color(color_field, title=legend_title),
            tooltip=tooltip,
        )
        .properties(width=width, height=height)
        .configure_axis(domain=False, ticks=False)
        .configure_view(stroke=None)
    )

    if title:
        chart = chart.properties(
            title=alt.TitleParams(
                text=wrap_title(title),
                anchor="start",
                fontSize=18,
                offset=10,
            )
        )

    return chart


def make_plot_row(md_text: str, plot_pane):
    common_style = {
        "border": "2px solid black",
        "box-shadow": "3px 3px 0 black",
        "padding": "20px",
    }
    return pn.Row(
        pn.Card(
            pn.pane.Markdown(md_text, width=280, margin=0),
            collapsible=False,
            hide_header=True,
            sizing_mode="stretch_height",
            styles=common_style,
        ),
        pn.Spacer(width=20),
        pn.Card(
            plot_pane,
            collapsible=False,
            hide_header=True,
            styles=common_style,
        ),
    )


def make_ranking_chart(
    df: pl.DataFrame,
    rank_first: int,
    rank_last: int,
    *,
    method: str = "avg_rank",
    top_n: int | None = None,
    title: str | None = None,
):
    """Ranking chart. Column N in [rank_first, rank_last) contains the choice
    name that the respondent placed at rank (N - rank_first + 1).
    method="avg_rank": horizontal bar of mean rank, sorted ascending (lower = preferred).
    method="top_n_count": count of appearances in the top `top_n` rank columns,
    sorted descending."""
    import re
    from collections import Counter as _C

    rank_cols = df.columns[rank_first:rank_last]
    if not rank_cols:
        return pn.pane.Markdown("_(no ranking columns)_")

    m = re.match(r"^(.*?)\s*\[Rank\s*\d+\]\s*$", rank_cols[0])
    base_title = m.group(1) if m else rank_cols[0]
    chart_title = title or base_title

    if method == "avg_rank":
        choice_to_ranks: dict[str, list[int]] = {}
        for i, c in enumerate(rank_cols):
            rank_pos = i + 1
            for v in df[c].cast(pl.Utf8).to_list():
                if v is None:
                    continue
                v_clean = v.strip()
                if not v_clean:
                    continue
                choice_to_ranks.setdefault(v_clean, []).append(rank_pos)

        if not choice_to_ranks:
            return pn.pane.Markdown(f"_(no ranking responses for: {chart_title})_")

        rows = [
            {"response": ch, "len": sum(ranks) / len(ranks)}
            for ch, ranks in choice_to_ranks.items()
        ]
        rows.sort(key=lambda r: r["len"])
        pdf = pd.DataFrame(rows)

        chart = so_style_bar_chart(
            pdf,
            title=f"{chart_title} — mean rank (lower = preferred)",
            normalize=False,
            label_format=lambda v: f"{v:.2f}",
            sort_ascending=True,
        )

    elif method == "top_n_count":
        effective_n = top_n if top_n is not None else len(rank_cols)
        considered = rank_cols[:effective_n]
        counter: _C[str] = _C()
        for c in considered:
            for v in df[c].cast(pl.Utf8).to_list():
                if v is None:
                    continue
                v_clean = v.strip()
                if not v_clean:
                    continue
                counter[v_clean] += 1

        if not counter:
            return pn.pane.Markdown(f"_(no ranking responses for: {chart_title})_")

        ordered = counter.most_common()
        pdf = pd.DataFrame({"response": [k for k, _ in ordered], "len": [v for _, v in ordered]})

        chart = so_style_bar_chart(
            pdf,
            title=f"{chart_title} — appearances in top {effective_n}",
            normalize=False,
            label_format=lambda v: f"{int(v):,}",
        )

    else:
        raise ValueError(f"Unknown method: {method!r}")

    return pn.pane.Vega(chart, sizing_mode="stretch_width")


def make_multi_vs_single_heatmap(
    df: pl.DataFrame,
    multi_first: int,
    multi_last: int,
    single_col: int,
    *,
    denominator: str,  # "single" or "trait"
    x_order: list[str] | None = None,
    x_exclude: list[str] | None = None,
    title: str | None = None,
    height: int = 320,
):
    """Cross-tab heatmap: rows = trait columns (multi-choice, "Yes" indicates the
    respondent selected the trait), columns = values of single_col.
    denominator="single": each cell = P(trait | single_value). Reads as a *rate*
        ("X% of respondents at this skill level picked this trait"). Cells in a
        column do NOT sum to 100% because traits aren't mutually exclusive.
    denominator="trait":  each cell = P(single_value | trait). Reads as a
        *composition* ("X% of respondents who picked this trait are at this
        skill level"). Cells in a row sum to 100%.
    denominator="lift":   each cell = P(single_value | trait) / P(single_value).
        Reads as a *lift / odds ratio* — how over- or under-represented this
        single_value is among trait-pickers relative to the population baseline.
        1.0 = same as baseline, >1.0 = over-represented, <1.0 = under-represented.
        Strips out the baseline imbalance between single_value groups."""
    import re

    if denominator not in {"single", "trait", "lift"}:
        raise ValueError(f"denominator must be 'single', 'trait', or 'lift', got {denominator!r}")

    multi_cols = df.columns[multi_first:multi_last]
    single_col_name = df.columns[single_col]

    cleaned = df.with_columns(
        pl.col(single_col_name)
        .cast(pl.Utf8)
        .str.strip_chars()
        .replace("", None)
        .fill_null("Skipped")
        .alias(single_col_name)
    )
    if x_exclude:
        cleaned = cleaned.filter(~pl.col(single_col_name).is_in(list(x_exclude)))

    bracket_re = re.compile(r"\[([^\]]+)\]\s*$")

    def trait_label(c: str) -> str:
        m = bracket_re.search(c)
        return m.group(1) if m else c

    trait_labels = [trait_label(c) for c in multi_cols]

    rows: list[dict] = []
    for trait_col, trait_lbl in zip(multi_cols, trait_labels):
        sub = cleaned.filter(pl.col(trait_col) == "Yes")
        if sub.height == 0:
            continue
        per_single = sub.group_by(single_col_name).len()
        for r in per_single.iter_rows(named=True):
            rows.append({
                "trait": trait_lbl,
                "single": r[single_col_name],
                "count": r["len"],
            })

    if not rows:
        return pn.pane.Markdown(f"_(no data for cross-tab: {single_col_name})_")

    long_df = pl.DataFrame(rows)

    if denominator == "single":
        denom = cleaned.group_by(single_col_name).len().rename({"len": "denom"})
        long_df = long_df.join(
            denom,
            left_on="single",
            right_on=single_col_name,
            how="left",
        )
        long_df = long_df.with_columns(
            pl.when(pl.col("denom") > 0)
            .then(pl.col("count") / pl.col("denom") * 100)
            .otherwise(0.0)
            .alias("value")
        )
        legend = "Rate (%)"
        tooltip_title = "Rate (%)"
        tooltip_format = ".1f"
        color_scale = alt.Scale()  # default sequential
    elif denominator == "trait":
        trait_totals = []
        for trait_col, trait_lbl in zip(multi_cols, trait_labels):
            n = cleaned.filter(pl.col(trait_col) == "Yes").height
            trait_totals.append({"trait": trait_lbl, "denom": n})
        denom = pl.DataFrame(trait_totals)
        long_df = long_df.join(denom, on="trait", how="left")
        long_df = long_df.with_columns(
            pl.when(pl.col("denom") > 0)
            .then(pl.col("count") / pl.col("denom") * 100)
            .otherwise(0.0)
            .alias("value")
        )
        legend = "Composition (%)"
        tooltip_title = "Composition (%)"
        tooltip_format = ".1f"
        color_scale = alt.Scale()
    else:  # "lift"
        total_cleaned = cleaned.height
        trait_totals = []
        for trait_col, trait_lbl in zip(multi_cols, trait_labels):
            n = cleaned.filter(pl.col(trait_col) == "Yes").height
            trait_totals.append({"trait": trait_lbl, "trait_total": n})
        trait_denom_df = pl.DataFrame(trait_totals)
        single_denom_df = (
            cleaned.group_by(single_col_name)
            .len()
            .rename({"len": "single_total"})
        )
        long_df = long_df.join(trait_denom_df, on="trait", how="left")
        long_df = long_df.join(
            single_denom_df,
            left_on="single",
            right_on=single_col_name,
            how="left",
        )
        # lift = (count / single_total) / (trait_total / total_cleaned)
        #      = (count * total_cleaned) / (single_total * trait_total)
        long_df = long_df.with_columns(
            pl.when(
                (pl.col("trait_total") > 0)
                & (pl.col("single_total") > 0)
                & (pl.lit(total_cleaned) > 0)
            )
            .then(
                pl.col("count") * pl.lit(float(total_cleaned))
                / (pl.col("trait_total") * pl.col("single_total"))
            )
            .otherwise(pl.lit(1.0))
            .alias("value")
        )
        legend = "Lift (× baseline)"
        tooltip_title = "Lift (×)"
        tooltip_format = ".2f"
        # Diverging scale centered at 1.0: white at 1, red below, blue above.
        color_scale = alt.Scale(scheme="redblue", domain=[0, 2], domainMid=1.0, clamp=True)

    if x_order is None:
        x_order_eff = sorted(long_df["single"].unique().to_list())
    else:
        present = set(long_df["single"].unique().to_list())
        x_order_eff = [v for v in x_order if v in present]
        x_order_eff.extend(sorted(present - set(x_order_eff)))

    pdf = long_df.to_pandas()

    chart_title = title or f"{single_col_name} (denominator: {denominator})"

    chart = (
        alt.Chart(pdf)
        .mark_rect()
        .encode(
            x=alt.X("single:N", sort=x_order_eff, title=single_col_name),
            y=alt.Y("trait:N", sort=trait_labels, title=None),
            color=alt.Color("value:Q", title=legend, scale=color_scale),
            tooltip=[
                alt.Tooltip("trait:N", title="Trait"),
                alt.Tooltip("single:N", title=single_col_name),
                alt.Tooltip("count:Q", title="Count"),
                alt.Tooltip("value:Q", title=tooltip_title, format=tooltip_format),
            ],
        )
        .properties(
            width="container",
            height=height,
            title=alt.TitleParams(
                text=wrap_title(chart_title),
                anchor="start",
                fontSize=18,
                offset=10,
            ),
        )
        .configure_axis(domain=False, ticks=False)
        .configure_view(stroke=None)
    )

    return pn.pane.Vega(chart, sizing_mode="stretch_width")
