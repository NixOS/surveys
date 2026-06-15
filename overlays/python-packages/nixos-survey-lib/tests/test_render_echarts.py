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
