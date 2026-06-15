from nixos_survey_lib.render_echarts import horizontal_bar
from nixos_survey_lib.types import Bin, ChartSpec


def test_horizontal_bar_basic_shape():
    bins = [
        Bin(label="Europe", count=60, percent=60.0),
        Bin(label="North America", count=20, percent=20.0),
        Bin(label="Asia", count=20, percent=20.0),
    ]
    spec = horizontal_bar(bins, title="Country")
    assert isinstance(spec, ChartSpec)
    opt = spec.option
    assert opt["yAxis"]["data"] == ["Asia", "North America", "Europe"]
    assert opt["series"][0]["type"] == "bar"
    assert opt["series"][0]["data"] == [20.0, 20.0, 60.0]
    assert opt["title"]["text"] == "Country"


def test_horizontal_bar_preserves_provided_height():
    bins = [Bin(label="A", count=1, percent=100.0)]
    spec = horizontal_bar(bins, height=480)
    assert spec.height == 480


def test_horizontal_bar_empty_bins():
    spec = horizontal_bar([])
    assert spec.option["yAxis"]["data"] == []
    assert spec.option["series"][0]["data"] == []


from nixos_survey_lib.render_echarts import heatmap
from nixos_survey_lib.types import CrossTab


def test_heatmap_basic_shape():
    ct = CrossTab(
        x_labels=["Beginner", "Advanced"],
        y_labels=["<2 years", "5+ years"],
        cells=[[80.0, 10.0], [5.0, 70.0]],
        cell_kind="rate_pct",
    )
    spec = heatmap(ct, title="Skill × Experience")
    opt = spec.option
    assert opt["xAxis"]["data"] == ["Beginner", "Advanced"]
    assert opt["yAxis"]["data"] == ["<2 years", "5+ years"]
    data = opt["series"][0]["data"]
    by = {(d[0], d[1]): d[2] for d in data}
    assert by[(0, 0)] == 80.0
    assert by[(1, 1)] == 70.0
    assert opt["series"][0]["type"] == "heatmap"
    assert opt["title"]["text"] == "Skill × Experience"


def test_heatmap_lift_uses_diverging_visualmap():
    ct = CrossTab(
        x_labels=["A"],
        y_labels=["t1"],
        cells=[[1.5]],
        cell_kind="lift",
    )
    spec = heatmap(ct)
    vm = spec.option["visualMap"]
    assert vm["min"] == 0
    assert vm["max"] == 2


def test_heatmap_annotate_percent_formatter():
    ct = CrossTab(
        x_labels=["A"],
        y_labels=["t1"],
        cells=[[42.0]],
        cell_kind="rate_pct",
    )
    spec = heatmap(ct, annotate=True)
    label = spec.option["series"][0]["label"]
    assert label["show"] is True
    assert label["formatter"] == "{@[2]}%"


def test_heatmap_annotate_lift_formatter():
    ct = CrossTab(
        x_labels=["A"],
        y_labels=["t1"],
        cells=[[1.5]],
        cell_kind="lift",
    )
    spec = heatmap(ct, annotate=True)
    label = spec.option["series"][0]["label"]
    assert label["show"] is True
    assert label["formatter"] == "{@[2]}×"


def test_heatmap_no_annotate_keeps_label_hidden():
    ct = CrossTab(
        x_labels=["A"],
        y_labels=["t1"],
        cells=[[42.0]],
        cell_kind="rate_pct",
    )
    spec = heatmap(ct)
    assert spec.option["series"][0]["label"] == {"show": False}


from nixos_survey_lib.render_echarts import diverging_bar


def test_diverging_bar_shape_and_colors():
    bins = [
        Bin(label="No issues", count=50, percent=50.0),
        Bin(label="Minor", count=20, percent=20.0),
        Bin(label="Moderate", count=10, percent=10.0),
        Bin(label="Severe resolved", count=6, percent=6.0),
        Bin(label="Severe stuck", count=4, percent=4.0),
        Bin(label="Did not know", count=5, percent=5.0),
        Bin(label="Not upgraded", count=5, percent=5.0),
    ]
    spec = diverging_bar(
        bins,
        positive=["No issues", "Minor"],
        negative=["Moderate", "Severe resolved", "Severe stuck"],
        neutral=["Did not know", "Not upgraded"],
    )
    opt = spec.option
    assert opt["yAxis"]["data"] == ["Other", "Severity"]
    series = {s["name"]: s for s in opt["series"]}
    # Positive labels: positive values on the Severity row, zero on Other.
    assert series["No issues"]["data"] == [0, 50.0]
    assert series["Minor"]["data"] == [0, 20.0]
    # Negative labels: negated values on the Severity row.
    assert series["Moderate"]["data"] == [0, -10.0]
    assert series["Severe stuck"]["data"] == [0, -4.0]
    # Neutral labels: positive values on the Other row only.
    assert series["Did not know"]["data"] == [5.0, 0]
    assert series["Not upgraded"]["data"] == [5.0, 0]
    # Hex colors only (never oklch).
    for s in opt["series"]:
        color = s["itemStyle"]["color"]
        assert color.startswith("#")
    # Positive uses a blue shade, negative an orange shade.
    assert series["No issues"]["itemStyle"]["color"] == "#4d6fb7"
    assert series["Moderate"]["itemStyle"]["color"] == "#e99861"
    # Neutral uses gray.
    assert series["Did not know"]["itemStyle"]["color"] == "#717171"
    # All severity series share one stack; neutral series share another.
    assert series["No issues"]["stack"] == "severity"
    assert series["Did not know"]["stack"] == "neutral"


from nixos_survey_lib.render_echarts import line_chart


def test_line_chart_series_per_y_label():
    ct = CrossTab(
        x_labels=["<1y", "1-2y", "3-4y"],
        y_labels=["Beginner", "Advanced"],
        cells=[[80.0, 20.0], [50.0, 50.0], [10.0, 90.0]],
        cell_kind="rate_pct",
    )
    spec = line_chart(ct)
    opt = spec.option
    assert opt["xAxis"]["data"] == ["<1y", "1-2y", "3-4y"]
    series = {s["name"]: s for s in opt["series"]}
    assert series["Beginner"]["type"] == "line"
    assert series["Beginner"]["data"] == [80.0, 50.0, 10.0]
    assert series["Advanced"]["data"] == [20.0, 50.0, 90.0]
    # No explicit color (inherits theme palette).
    assert "color" not in series["Beginner"]
    assert "itemStyle" not in series["Beginner"]


from nixos_survey_lib.render_echarts import ranking_bar
from nixos_survey_lib.types import Ranked


def test_ranking_bar_avg_rank_formatter():
    ranked = [
        Ranked(label="Docs", value=2.28, method="avg_rank"),
        Ranked(label="Nixpkgs", value=3.47, method="avg_rank"),
    ]
    spec = ranking_bar(ranked)
    opt = spec.option
    assert opt["yAxis"]["data"] == ["Nixpkgs", "Docs"]
    assert opt["series"][0]["data"] == [3.47, 2.28]


def test_ranking_bar_top_n_count_formatter():
    ranked = [
        Ranked(label="Wiki", value=2313, method="top_n_count"),
        Ranked(label="Manuals", value=1995, method="top_n_count"),
    ]
    spec = ranking_bar(ranked)
    opt = spec.option
    assert opt["series"][0]["data"] == [1995, 2313]
