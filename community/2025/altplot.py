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


def make_multi_bar_chart_pane(df, first, last, min_percent=0.0):
    reduced, title = reduce_multi_choice_to_single_column(df, first, last)

    if min_percent > 0:
        reduced = bucket_rare_categories_df(reduced, 0, min_percent=min_percent)

    pdf = reduced.to_pandas()

    chart = so_style_bar_chart(pdf, title=title, normalize=False, label_order=None)
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


def make_text_frequency_chart(
    df: pl.DataFrame,
    col: int,
    *,
    top_n: int = 20,
    min_token_len: int = 2,
    extra_stopwords: list[str] | None = None,
    title: str | None = None,
):
    """Top-N token frequency bar chart for a free-text column.
    Reuses so_style_bar_chart with a count formatter."""
    from dfhelpers import tokenize_text_column

    counts = tokenize_text_column(
        df, col,
        min_token_len=min_token_len,
        extra_stopwords=extra_stopwords,
    )
    col_name = df.columns[col]
    chart_title = title or col_name

    if not counts:
        return pn.pane.Markdown(f"_(no tokens for: {col_name})_")

    top = sorted(counts.items(), key=lambda kv: -kv[1])[:top_n]
    pdf = pd.DataFrame({"response": [t for t, _ in top], "len": [c for _, c in top]})

    chart = so_style_bar_chart(
        pdf,
        title=chart_title,
        normalize=False,
        label_format=lambda v: f"{int(v):,}",
    )
    return pn.pane.Vega(chart, sizing_mode="stretch_width")


def make_wordcloud_pane(
    df: pl.DataFrame,
    col: int,
    *,
    min_token_len: int = 2,
    extra_stopwords: list[str] | None = None,
    width: int = 640,
    height: int = 320,
    background_color: str = "white",
):
    """Render a word cloud PNG for a free-text column."""
    from io import BytesIO
    from wordcloud import WordCloud
    from dfhelpers import tokenize_text_column

    counts = tokenize_text_column(
        df, col,
        min_token_len=min_token_len,
        extra_stopwords=extra_stopwords,
    )
    if not counts:
        col_name = df.columns[col]
        return pn.pane.Markdown(f"_(no tokens for: {col_name})_")

    wc = WordCloud(
        width=width,
        height=height,
        background_color=background_color,
    ).generate_from_frequencies(counts)

    buf = BytesIO()
    wc.to_image().save(buf, format="PNG")
    buf.seek(0)
    return pn.pane.PNG(buf.read(), width=width, height=height)
