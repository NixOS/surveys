from pathlib import Path

import altair as alt
import panel as pn
import polars as pl

pn.extension("vega")

csv_data = Path(__file__).parent / "nix-community-survey-2025-completed-responses.csv"
df = pl.read_csv(csv_data)

col_name = df.columns[5]


counts = (
    df.select(
        pl.col(col_name)
        .cast(pl.Utf8)
        .str.strip_chars()
        .replace("", None)
        .fill_null("Skipped")
        .alias("response")
    )
    .group_by("response")
    .len()
    .sort("len", descending=True)
)

pdf = counts.to_pandas()
print(counts)

chart = (
    alt.Chart(pdf, title=col_name)
    .mark_bar()
    .encode(
        y=alt.Y("response:N", sort="-x", title=None),
        x=alt.X("len:Q", title="Count"),
        tooltip=[alt.Tooltip("response:N"), alt.Tooltip("len:Q", title="Count")],
    )
    .properties(height=500)
)

pn.Column(
    f"## {col_name}",
    pn.pane.Vega(chart, sizing_mode="stretch_width"),
).servable()
