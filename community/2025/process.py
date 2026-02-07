from pathlib import Path

import altair as alt
import panel as pn
import polars as pl


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
    label_width: int = 240,
    bar_width: int = 320,
    step: int = 22,  # controls row height => constant bar thickness
    bar_size: int = 16,  # actual bar thickness
    gap: int = 16,  # gap between label column and bars
):
    pdf = pdf.copy()

    # Order categories by count (so y-domain is stable across concatenated charts)
    pdf = pdf.sort_values("len", ascending=False)
    order = pdf["response"].tolist()

    total = float(pdf["len"].sum()) if len(pdf) else 0.0
    pdf["pct"] = (pdf["len"] / total * 100.0) if total > 0 else 0.0
    pdf["pct_label"] = pdf["pct"].map(lambda v: f"{v:.1f}%")

    max_len = float(pdf["len"].max()) if len(pdf) else 1.0

    y = alt.Y("response:N", sort=order, axis=None)
    y_bars = alt.Y(
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

    # Left column: labels (fixed width, left-aligned)
    labels = (
        alt.Chart(pdf)
        .mark_text(
            align="left",
            baseline="middle",
            dx=0,
            fontSize=12,
        )
        .encode(
            y=y,
            x=alt.value(0),  # <-- anchor labels at the left edge
            text="response:N",
        )
        .properties(width=label_width, height=alt.Step(step))
    )

    # Right column: bars + percent labels (no axes)
    base = alt.Chart(pdf).encode(
        y=y_bars,
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

    # Combine: fixed label column + bars column
    return (
        alt.hconcat(labels, bars_block, spacing=gap)
        .resolve_scale(y="shared")
        .properties(
            title=alt.TitleParams(text=title, anchor="start", fontSize=18, offset=10)
        )
        .configure_view(strokeWidth=0)
    )


def make_simple_bar_chart_pane(df, column):
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

    chart = so_style_bar_chart(pdf, title=col_name)
    altair_pane = pn.pane.Vega(chart, sizing_mode="stretch_width")

    return altair_pane


csv_data = Path(__file__).parent / "nix-community-survey-2025-completed-responses.csv"
df = pl.read_csv(csv_data)

pn.extension("vega")

app = pn.Column(
    pn.pane.Markdown(
        "# NixOS Community Survey 2025\nSurvey results", margin=(0, 0, 10, 0)
    ),
    pn.Row(
        pn.Card(
            pn.pane.Markdown(
                """
                # Country
                European responses increased from 52% to 60%.
                North American responses decreased from 27.5% to 21.3%.
                The remaining responses changed less than 1% from the previous year.
                """,
                width=320,
            ),
            styles={"border": "2px solid black", "box-shadow": "3px 3px 0 black"},
            hide_header=True,
            sizing_mode="stretch_height",
            collapsible=False,
        ),
        pn.Spacer(width=20),
        pn.Card(
            make_simple_bar_chart_pane(df, 5),
            collapsible=False,
            styles={"border": "2px solid black", "box-shadow": "3px 3px 0 black"},
            hide_header=True,
        ),
    ),
    pn.Spacer(height=20),
    pn.Row(
        pn.Card(
            pn.pane.Markdown(
                """
                # Age
                The curve has flattened and shifted.
                The largest age group of 25-34 decreased from 35.6% to 30.7%.
                The 35-44 age group also decreased from 22.7% to 19.4%.
                Age groups under 25 or over 44 increased between 0.4% and 3.1%.
                """,
                width=320,
            ),
            styles={"border": "2px solid black", "box-shadow": "3px 3px 0 black"},
            hide_header=True,
            sizing_mode="stretch_height",
            collapsible=False,
        ),
        pn.Spacer(width=20),
        pn.Card(
            make_simple_bar_chart_pane(df, 6),
            collapsible=False,
            styles={"border": "2px solid black", "box-shadow": "3px 3px 0 black"},
            hide_header=True,
        ),
    ),
    pn.Spacer(height=20),
    pn.Row(
        pn.Card(
            pn.pane.Markdown(
                """
                # Gender Identity
                """,
                width=320,
            ),
            styles={"border": "2px solid black", "box-shadow": "3px 3px 0 black"},
            hide_header=True,
            sizing_mode="stretch_height",
            collapsible=False,
        ),
        pn.Spacer(width=20),
        pn.Card(
            make_simple_bar_chart_pane(df, 7),
            collapsible=False,
            styles={"border": "2px solid black", "box-shadow": "3px 3px 0 black"},
            hide_header=True,
        ),
    ),
    pn.Spacer(height=20),
    pn.Row(
        pn.Card(
            pn.pane.Markdown(
                """
                # Transgender Identity
                """,
                width=320,
            ),
            styles={"border": "2px solid black", "box-shadow": "3px 3px 0 black"},
            hide_header=True,
            sizing_mode="stretch_height",
            collapsible=False,
        ),
        pn.Spacer(width=20),
        pn.Card(
            make_simple_bar_chart_pane(df, 8),
            collapsible=False,
            styles={"border": "2px solid black", "box-shadow": "3px 3px 0 black"},
            hide_header=True,
        ),
    ),
    sizing_mode="stretch_width",
    margin=20,
)
app.servable()
