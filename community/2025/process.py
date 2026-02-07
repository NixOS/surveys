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

    bars = base.mark_bar(cornerRadiusEnd=3)

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

    chart = pretty_bar_chart(pdf, title=col_name)
    altair_pane = pn.pane.Vega(chart, sizing_mode="stretch_width")

    return altair_pane


csv_data = Path(__file__).parent / "nix-community-survey-2025-completed-responses.csv"
df = pl.read_csv(csv_data)

community_makeup = [
    make_simple_bar_chart_pane(df, 5),
    make_simple_bar_chart_pane(df, 6),
    make_simple_bar_chart_pane(df, 7),
    make_simple_bar_chart_pane(df, 8),
]

pn.extension("vega")

app = pn.Column(
    pn.pane.Markdown(
        "# NixOS Community Survey 2025\nSurvey results", margin=(0, 0, 10, 0)
    ),
    pn.Card(
        *community_makeup,
        title="Community Makeup",
        collapsible=False,
    ),
    sizing_mode="stretch_width",
    margin=20,
)
app.servable()
