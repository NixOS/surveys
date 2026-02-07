import textwrap
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
    bar_width: int = 480,
    step: int = 24,  # controls row height => constant bar thickness
    bar_size: int = 16,  # actual bar thickness
    gap: int = 0,  # gap between label column and bars
    label_order: list[str] | None = None,
):
    pdf = pdf.copy()

    # Default: order by count descending (like SO)
    if label_order is None:
        pdf = pdf.sort_values("len", ascending=False)
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

    total = float(pdf["len"].sum()) if len(pdf) else 0.0
    pdf["pct"] = (pdf["len"] / total * 100.0) if total > 0 else 0.0
    pdf["pct_label"] = pdf["pct"].map(lambda v: f"{v:.1f}%")
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

    labels = (
        alt.Chart(pdf)
        .mark_text(
            align="left",
            baseline="middle",
            fontSize=12,
        )
        .encode(
            y=y_grid,
            x=alt.value(0),  # pin to left edge
            text="response:N",
        )
        .properties(width=label_width + gap, height=alt.Step(step))
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


def wrap_title(s: str, width: int = 80) -> list[str]:
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


def make_plot_row(md_text: str, plot_pane):
    common_style = {"border": "2px solid black", "box-shadow": "3px 3px 0 black"}
    return pn.Row(
        pn.Card(
            pn.pane.Markdown(md_text, width=320),
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


csv_data = Path(__file__).parent / "nix-community-survey-2025-completed-responses.csv"
df = pl.read_csv(csv_data)

pn.extension("vega")

app = pn.Column(
    pn.pane.Markdown(
        "# NixOS Community Survey 2025\nSurvey results", margin=(0, 0, 10, 0)
    ),
    make_plot_row(
        md_text="""
                # Country
                European responses increased from 52% to 60%.
                North American responses decreased from 27.5% to 21.3%.
                The remaining responses changed less than 1% from the previous year.
                """,
        plot_pane=make_simple_bar_chart_pane(df, 5),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Age
                The curve has flattened and shifted.
                The largest age group of 25-34 decreased from 35.6% to 30.7%.
                The 35-44 age group also decreased from 22.7% to 19.4%.
                Age groups under 25 or over 44 increased between 0.4% and 3.1%.
                """,
        plot_pane=make_simple_bar_chart_pane(
            df,
            6,
            label_order=[
                "Under 18",
                "18-24",
                "25-34",
                "35-44",
                "45-54",
                "55-64",
                "65 or older",
                "Prefer not to say",
                "Skipped",
            ],
        ),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Gender Identity
                """,
        plot_pane=make_simple_bar_chart_pane(df, 7),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Transgender Identity
                """,
        plot_pane=make_simple_bar_chart_pane(df, 8),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Years Coding
                There are more fine grained bins for 10+ years of experience compared to previous years.
                The groups with 4 or less years of experience have increased.
                The groups with 5 or more years of experience have decreased.
                """,
        plot_pane=make_simple_bar_chart_pane(
            df,
            9,
            label_order=[
                "I have never programmed",
                "Less than 1 year",
                "1 to 4 years",
                "5 to 9 years",
                "10 to 14 years",
                "15 to 19 years",
                "20 to 24 years",
                "25 to 29 years",
                "30 to 34 years",
                "35 to 39 years",
                "40 to 44 years",
                "45 to 49 years",
                "More than 50 years",
                "Prefer not to say",
                "Skipped",
            ],
        ),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Role
                """,
        plot_pane=make_simple_bar_chart_pane(df, 10),
    ),
    pn.Spacer(height=20),
    make_plot_row(
        md_text="""
                # Industry
                """,
        plot_pane=make_simple_bar_chart_pane(df, 11),
    ),
    sizing_mode="stretch_width",
    margin=20,
)
app.servable()
