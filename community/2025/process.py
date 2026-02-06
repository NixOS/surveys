from pathlib import Path

import altair as alt
import panel as pn
import polars as pl


def pretty_bar_chart(pdf, title, max_items=25, height_step=18):
    # Optional: keep top N
    if len(pdf) > max_items:
        top = pdf.iloc[:max_items].copy()
        other = pdf.iloc[max_items:]["len"].sum()
        top.loc[len(top)] = {"response": "Other", "len": int(other)}
        pdf = top

    # Make height scale with number of categories
    height = max(240, len(pdf) * height_step)

    base = alt.Chart(pdf).encode(
        x=alt.X(
            "len:Q",
            title=None,
            axis=alt.Axis(
                labelFontSize=12,
                ticks=False,
                grid=True,
            ),
        ),
        y=alt.Y(
            "response_short:N",
            sort="-x",
            title=None,
            axis=alt.Axis(
                labelLimit=320,  # prevent overly wide labels
                labelFontSize=12,
                ticks=False,
            ),
        ),
        tooltip=[alt.Tooltip("response:N", title="Response"), alt.Tooltip("len:Q")],
    )

    bars = base.mark_bar(cornerRadiusEnd=3)

    labels = base.mark_text(
        align="left",
        baseline="middle",
        dx=4,  # nudge label right
        fontSize=12,
    ).encode(text=alt.Text("len:Q"))

    chart = (
        (bars + labels)
        .properties(
            title=alt.TitleParams(
                text=title,
                fontSize=18,
                anchor="start",
                subtitle=["Counts of responses (blank → None)"],
                subtitleFontSize=12,
            ),
            height=height,
        )
        .configure_view(strokeWidth=0)  # remove outer border
        .configure_axis(
            domain=False,  # remove axis lines
            labelColor="#222",
            gridColor="#ddd",
            gridOpacity=0.35,
        )
        .configure_title(offset=10)
    )

    return chart


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


pn.extension("vega")

csv_data = Path(__file__).parent / "nix-community-survey-2025-completed-responses.csv"
df = pl.read_csv(csv_data)

where_do_you_live = make_simple_bar_chart_pane(df, 5)
age_in_years = make_simple_bar_chart_pane(df, 6)
gender_identity = make_simple_bar_chart_pane(df, 7)

app = pn.Column(
    pn.pane.Markdown("# NixOS Community Survey 2025\nSurvey results", margin=(0, 0, 10, 0)),
    pn.Card(where_do_you_live, title="Responses", collapsible=False),
    pn.Card(age_in_years, title="Responses", collapsible=False),
    pn.Card(gender_identity, title="Responses", collapsible=False),
    sizing_mode="stretch_width",
    margin=20,
)
app.servable()
