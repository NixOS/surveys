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


def test_heatmap_data_values_rounded_to_one_decimal():
    # Cell values with more than 1 decimal place must be rounded in the data
    # array so annotation labels (e.g. "{@[2]}%") display "41.4%" not "41.378378%".
    ct = CrossTab(
        x_labels=["A"],
        y_labels=["t1"],
        cells=[[41.378378]],
        cell_kind="rate_pct",
    )
    spec = heatmap(ct, annotate=True)
    data = spec.option["series"][0]["data"]
    assert data[0][2] == 41.4


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


from nixos_survey_lib.render_echarts import likert_bar


def test_likert_bar_100pct_stacked():
    bins = [
        Bin(label="Strongly agree", count=40, percent=40.0),
        Bin(label="Agree", count=30, percent=30.0),
        Bin(label="Disagree", count=15, percent=15.0),
        Bin(label="Strongly disagree", count=10, percent=10.0),
        Bin(label="No opinion", count=5, percent=5.0),
    ]
    spec = likert_bar(
        bins,
        positive=["Strongly agree", "Agree"],
        negative=["Disagree", "Strongly disagree"],
        neutral=["No opinion"],
    )
    opt = spec.option
    series = opt["series"]
    # Segment count == len(positive) + len(negative) + len(neutral).
    assert len(series) == 5
    # All series share one stack.
    assert all(s["stack"] == "likert" for s in series)
    # No negative values anywhere.
    for s in series:
        for v in s["data"]:
            assert v >= 0


def test_likert_bar_segment_order():
    bins = [
        Bin(label="Strongly agree", count=40, percent=40.0),
        Bin(label="Agree", count=30, percent=30.0),
        Bin(label="Disagree", count=15, percent=15.0),
        Bin(label="Strongly disagree", count=10, percent=10.0),
        Bin(label="No opinion", count=5, percent=5.0),
    ]
    spec = likert_bar(
        bins,
        positive=["Strongly agree", "Agree"],
        negative=["Disagree", "Strongly disagree"],
        neutral=["No opinion"],
    )
    series = spec.option["series"]
    names = [s["name"] for s in series]
    # Positive first, then negative, then neutral.
    assert names == ["Strongly agree", "Agree", "Disagree", "Strongly disagree", "No opinion"]


def test_likert_bar_hex_colors_and_distinct_neutrals():
    bins = [
        Bin(label="Yes", count=60, percent=60.0),
        Bin(label="No", count=20, percent=20.0),
        Bin(label="Maybe", count=10, percent=10.0),
        Bin(label="N/A", count=10, percent=10.0),
    ]
    spec = likert_bar(
        bins,
        positive=["Yes"],
        negative=["No"],
        neutral=["Maybe", "N/A"],
    )
    series = {s["name"]: s for s in spec.option["series"]}
    # All colors are hex literals.
    for s in spec.option["series"]:
        assert s["itemStyle"]["color"].startswith("#")
    # Two neutral segments must have DIFFERENT colors.
    assert series["Maybe"]["itemStyle"]["color"] != series["N/A"]["itemStyle"]["color"]


def test_likert_bar_label_formatter():
    bins = [Bin(label="Yes", count=100, percent=100.0)]
    spec = likert_bar(bins, positive=["Yes"], negative=[], neutral=[])
    series = spec.option["series"]
    assert series[0]["label"]["formatter"] == "{c}%"


def test_likert_bar_tooltip_and_legend():
    bins = [Bin(label="Yes", count=100, percent=100.0)]
    spec = likert_bar(bins, positive=["Yes"], negative=[], neutral=[])
    opt = spec.option
    assert opt["tooltip"]["trigger"] == "item"
    assert opt["tooltip"]["formatter"] == "{a}: {c}%"
    assert "legend" in opt
    assert opt["legend"].get("type") != "scroll"


def test_likert_bar_title():
    bins = [Bin(label="Yes", count=100, percent=100.0)]
    spec = likert_bar(bins, positive=["Yes"], negative=[], neutral=[], title="My question")
    assert spec.option["title"]["text"] == "My question"


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



from nixos_survey_lib.render_echarts import lollipop


def test_lollipop_shape():
    bins = [
        Bin(label="Linux", count=90, percent=90.0),
        Bin(label="macOS", count=30, percent=30.0),
        Bin(label="Windows", count=10, percent=10.0),
    ]
    spec = lollipop(bins)
    opt = spec.option
    # Reversed so largest is at the top, like horizontal_bar.
    assert opt["yAxis"]["data"] == ["Windows", "macOS", "Linux"]
    # Two series: stem (bar) first, then dot (pictorialBar) on top.
    assert len(opt["series"]) == 2
    stem, dot = opt["series"]
    # Stem: thin bar series.
    assert stem["type"] == "bar"
    assert stem["barWidth"] == 2
    assert stem["itemStyle"]["color"] == "#4d6fb7"
    assert stem["data"] == [10.0, 30.0, 90.0]
    assert stem["silent"] is True
    # Dot: pictorialBar carrying the label.
    assert dot["type"] == "pictorialBar"
    assert dot["symbol"] == "circle"
    assert dot["symbolPosition"] == "end"
    assert dot["data"] == [10.0, 30.0, 90.0]
    assert dot["itemStyle"]["color"] == "#4d6fb7"
    assert dot["label"]["show"] is True
    assert dot["label"]["formatter"] == "{c}%"
    # Tooltip uses item trigger so two series don't produce duplicate rows.
    assert opt["tooltip"]["trigger"] == "item"


from nixos_survey_lib.render_echarts import rank_distribution_bar
from nixos_survey_lib.types import RankDistribution, RankDistItem


def test_rank_distribution_bar_shape_and_colors():
    dist = RankDistribution(
        segment_labels=["#1", "#2", "Unranked"],
        items=[
            RankDistItem(label="Docs", percents=[60.0, 30.0, 10.0]),
            RankDistItem(label="Wiki", percents=[20.0, 20.0, 60.0]),
        ],
    )
    spec = rank_distribution_bar(dist)
    opt = spec.option
    # Reversed so the top item (Docs) sits at the top of a bottom-up y-axis.
    assert opt["yAxis"]["data"] == ["Wiki", "Docs"]
    series = {s["name"]: s for s in opt["series"]}
    assert set(series) == {"#1", "#2", "Unranked"}
    # All series stacked together.
    assert series["#1"]["stack"] == "total"
    assert series["#2"]["stack"] == "total"
    # Reversed data alignment: Wiki first, Docs second.
    assert series["#1"]["data"] == [20.0, 60.0]
    assert series["Unranked"]["data"] == [60.0, 10.0]
    # Hex colors; top rank darkest blue (well-separated from later ranks), Unranked gray.
    assert series["#1"]["itemStyle"]["color"] == "#15213a"
    assert series["Unranked"]["itemStyle"]["color"] == "#aeaeae"
    # Rank bands must be visually distinct from each other and from gray_light.
    rank1_color = series["#1"]["itemStyle"]["color"]
    rank2_color = series["#2"]["itemStyle"]["color"]
    assert rank1_color != rank2_color
    for s in opt["series"]:
        assert s["itemStyle"]["color"].startswith("#")


def test_rank_distribution_bar_empty():
    dist = RankDistribution(segment_labels=[], items=[])
    spec = rank_distribution_bar(dist)
    assert spec.option["series"] == []
    assert spec.option["yAxis"]["data"] == []


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _perceived_lightness(h: str) -> float:
    """Approximate perceived lightness (0–1) using sRGB luminance formula."""
    r, g, b = _hex_to_rgb(h)
    return 0.2126 * (r / 255) + 0.7152 * (g / 255) + 0.0722 * (b / 255)


def test_rank_distribution_bar_monotonic_lightness_n3():
    """3 ranked + 1 unranked: the 3 ranked colors must be strictly darker→lighter."""
    dist = RankDistribution(
        segment_labels=["#1", "#2", "#3", "Unranked"],
        items=[RankDistItem(label="X", percents=[25.0, 25.0, 25.0, 25.0])],
    )
    spec = rank_distribution_bar(dist)
    series = {s["name"]: s for s in spec.option["series"]}
    ranked = ["#1", "#2", "#3"]
    lightness = [_perceived_lightness(series[r]["itemStyle"]["color"]) for r in ranked]
    # Each successive rank must be strictly lighter.
    for i in range(len(lightness) - 1):
        assert lightness[i] < lightness[i + 1], (
            f"rank {i+1} ({lightness[i]:.3f}) not darker than rank {i+2} ({lightness[i+1]:.3f})"
        )
    # Rank 1 is the darkest of all ranked colors.
    assert lightness[0] == min(lightness)


def test_rank_distribution_bar_monotonic_lightness_n5():
    """5 ranked + 1 unranked: ranked colors must be strictly darker→lighter."""
    dist = RankDistribution(
        segment_labels=["#1", "#2", "#3", "#4", "#5", "Unranked"],
        items=[RankDistItem(label="X", percents=[16.0, 16.0, 16.0, 16.0, 16.0, 20.0])],
    )
    spec = rank_distribution_bar(dist)
    series = {s["name"]: s for s in spec.option["series"]}
    ranked = ["#1", "#2", "#3", "#4", "#5"]
    lightness = [_perceived_lightness(series[r]["itemStyle"]["color"]) for r in ranked]
    for i in range(len(lightness) - 1):
        assert lightness[i] < lightness[i + 1], (
            f"rank {i+1} ({lightness[i]:.3f}) not darker than rank {i+2} ({lightness[i+1]:.3f})"
        )
    assert lightness[0] == min(lightness)


def test_rank_distribution_bar_even_spacing_n3():
    """For N=3 ranked segments, even spacing picks ramp indices 0, 3, 6 (first, middle, last)."""
    from nixos_survey_lib.render_echarts import _RANK_DIST_BLUES
    dist = RankDistribution(
        segment_labels=["#1", "#2", "#3", "Unranked"],
        items=[RankDistItem(label="X", percents=[25.0, 25.0, 25.0, 25.0])],
    )
    spec = rank_distribution_bar(dist)
    series_by_name = {s["name"]: s for s in spec.option["series"]}
    ramp = _RANK_DIST_BLUES
    n = len(ramp)
    N = 3
    expected = [ramp[round(i * (n - 1) / max(N - 1, 1))] for i in range(N)]
    assert series_by_name["#1"]["itemStyle"]["color"] == expected[0]
    assert series_by_name["#2"]["itemStyle"]["color"] == expected[1]
    assert series_by_name["#3"]["itemStyle"]["color"] == expected[2]


def test_rank_distribution_bar_even_spacing_n5():
    """For N=5 ranked segments, even spacing picks ramp indices 0, 1~2, 3~4, 5, 6."""
    from nixos_survey_lib.render_echarts import _RANK_DIST_BLUES
    dist = RankDistribution(
        segment_labels=["#1", "#2", "#3", "#4", "#5", "Unranked"],
        items=[RankDistItem(label="X", percents=[16.0, 16.0, 16.0, 16.0, 16.0, 20.0])],
    )
    spec = rank_distribution_bar(dist)
    series_by_name = {s["name"]: s for s in spec.option["series"]}
    ramp = _RANK_DIST_BLUES
    n = len(ramp)
    N = 5
    expected = [ramp[round(i * (n - 1) / max(N - 1, 1))] for i in range(N)]
    ranked = ["#1", "#2", "#3", "#4", "#5"]
    for rank, exp_color in zip(ranked, expected):
        assert series_by_name[rank]["itemStyle"]["color"] == exp_color


def test_likert_bar_all_segment_colors_distinct():
    """2-positive / 3-negative / 2-neutral: all 7 segment colors must be unique."""
    bins = [
        Bin(label="No issues", count=30, percent=30.0),
        Bin(label="Minor issues", count=20, percent=20.0),
        Bin(label="Moderate issues", count=15, percent=15.0),
        Bin(label="Severe resolved", count=10, percent=10.0),
        Bin(label="Severe stuck", count=10, percent=10.0),
        Bin(label="N/A", count=8, percent=8.0),
        Bin(label="Unknown", count=7, percent=7.0),
    ]
    spec = likert_bar(
        bins,
        positive=["No issues", "Minor issues"],
        negative=["Moderate issues", "Severe resolved", "Severe stuck"],
        neutral=["N/A", "Unknown"],
    )
    colors = [s["itemStyle"]["color"] for s in spec.option["series"]]
    assert len(colors) == 7
    assert len(set(colors)) == 7, f"Duplicate colors found: {colors}"


from nixos_survey_lib.render_echarts import upset
from nixos_survey_lib.types import Combination


def _upset_inputs():
    combos = [
        Combination(members=("A",), size=10),
        Combination(members=("A", "B"), size=6),
        Combination(members=("B", "C"), size=5),
    ]
    set_totals = [("A", 16), ("B", 11), ("C", 5)]
    return combos, set_totals


def test_upset_has_three_grids():
    combos, set_totals = _upset_inputs()
    spec = upset(combos, set_totals, 0, height=400)
    grids = spec.option["grid"]
    assert isinstance(grids, list)
    assert len(grids) == 3


def test_upset_top_bar_wiring_and_sizes():
    combos, set_totals = _upset_inputs()
    opt = upset(combos, set_totals, 0, height=400).option
    bar = next(s for s in opt["series"] if s["type"] == "bar" and s["xAxisIndex"] == 0)
    assert bar["yAxisIndex"] == 0
    assert bar["data"] == [10, 6, 5]


def test_upset_set_rows_and_left_bar():
    combos, set_totals = _upset_inputs()
    opt = upset(combos, set_totals, 0, height=400).option
    # The dot-matrix y-axis (index 1) lists the sets in set_totals order.
    yaxes = opt["yAxis"]
    assert yaxes[1]["data"] == ["A", "B", "C"]
    assert yaxes[1]["inverse"] is True
    # Left bar (xAxisIndex 2 / yAxisIndex 2) carries per-set totals.
    left = next(s for s in opt["series"] if s["type"] == "bar" and s["xAxisIndex"] == 2)
    assert left["yAxisIndex"] == 2
    assert left["data"] == [16, 11, 5]
    # Left value axis grows leftward.
    assert opt["xAxis"][2]["inverse"] is True


def test_upset_dot_matrix_fill_state():
    combos, set_totals = _upset_inputs()
    opt = upset(combos, set_totals, 0, height=400).option
    scatter = next(s for s in opt["series"] if s["type"] == "scatter")
    assert scatter["xAxisIndex"] == 1
    assert scatter["yAxisIndex"] == 1
    # Index points by (column, row).
    points = {tuple(d["value"]): d["itemStyle"]["color"] for d in scatter["data"]}
    # Column 0 is (A,): row 0 (A) filled, rows 1 (B) and 2 (C) faded.
    assert points[(0, 0)] == "#5277c3"
    assert points[(0, 1)] == "#c9c9c9"
    assert points[(0, 2)] == "#c9c9c9"
    # Column 2 is (B, C): row 0 (A) faded, rows 1 (B) and 2 (C) filled.
    assert points[(2, 0)] == "#c9c9c9"
    assert points[(2, 1)] == "#5277c3"
    assert points[(2, 2)] == "#5277c3"


def test_upset_subtext_reports_dropped():
    combos, set_totals = _upset_inputs()
    opt = upset(combos, set_totals, 4, height=400).option
    assert "4" in opt["title"]["subtext"]


def test_upset_no_subtext_when_nothing_dropped():
    combos, set_totals = _upset_inputs()
    opt = upset(combos, set_totals, 0, height=400).option
    # No dropped combos -> no subtext (or empty), never a misleading "0 ...".
    subtext = opt.get("title", {}).get("subtext", "")
    assert subtext == ""


def test_upset_bars_emit_no_explicit_color():
    combos, set_totals = _upset_inputs()
    opt = upset(combos, set_totals, 0, height=400).option
    for s in opt["series"]:
        if s["type"] == "bar":
            assert "color" not in s
            assert "color" not in s.get("itemStyle", {})


def test_upset_no_oklch_anywhere():
    combos, set_totals = _upset_inputs()
    opt = upset(combos, set_totals, 0, height=400).option
    import json
    assert "oklch" not in json.dumps(opt).lower()


def test_upset_connector_lines_span_filled_rows():
    # combos: (A,) single filled row -> no connector;
    #         (A, B) rows 0..1 -> connector from [1,0] to [1,1];
    #         (B, C) rows 1..2 -> connector from [2,1] to [2,2].
    combos, set_totals = _upset_inputs()
    opt = upset(combos, set_totals, 0, height=400).option
    line_series = [
        s for s in opt["series"]
        if s["type"] == "line" and s.get("xAxisIndex") == 1
    ]
    # Map each connector by its constant column index.
    spans = {}
    for s in line_series:
        col = s["data"][0][0]
        rows = sorted(pt[1] for pt in s["data"])
        spans[col] = (rows[0], rows[-1])
    # Column 0 (A,) has a single filled row -> no connector.
    assert 0 not in spans
    # Column 1 (A,B) spans rows 0..1.
    assert spans[1] == (0, 1)
    # Column 2 (B,C) spans rows 1..2.
    assert spans[2] == (1, 2)


def test_upset_connector_lines_use_hex_color():
    combos, set_totals = _upset_inputs()
    opt = upset(combos, set_totals, 0, height=400).option
    for s in opt["series"]:
        if s["type"] == "line" and s.get("xAxisIndex") == 1:
            color = s.get("lineStyle", {}).get("color", "")
            assert color.startswith("#")


from nixos_survey_lib.render_echarts import sankey


def test_sankey_basic_shape():
    nodes = ["All", "Knew", "Didn't know"]
    links = [
        {"source": "All", "target": "Knew", "value": 90},
        {"source": "All", "target": "Didn't know", "value": 10},
    ]
    spec = sankey(nodes, links)
    opt = spec.option
    assert opt["series"][0]["type"] == "sankey"
    assert opt["series"][0]["data"] == [
        {"name": "All"},
        {"name": "Knew"},
        {"name": "Didn't know"},
    ]
    assert opt["series"][0]["links"] == [
        {"source": "All", "target": "Knew", "value": 90},
        {"source": "All", "target": "Didn't know", "value": 10},
    ]


def test_sankey_has_tooltip_and_no_axes():
    spec = sankey(["A", "B"], [{"source": "A", "target": "B", "value": 5}])
    opt = spec.option
    assert "tooltip" in opt
    assert "grid" not in opt
    assert "xAxis" not in opt
    assert "yAxis" not in opt


def test_sankey_emits_no_explicit_colors():
    spec = sankey(["A", "B"], [{"source": "A", "target": "B", "value": 5}])
    series = spec.option["series"][0]
    # Theme palette is inherited; the renderer must not pin colors.
    assert "color" not in spec.option
    assert "color" not in series
    for node in series["data"]:
        assert "itemStyle" not in node


def test_sankey_respects_provided_height():
    spec = sankey(["A", "B"], [{"source": "A", "target": "B", "value": 5}], height=520)
    assert spec.height == 520


def test_sankey_default_height():
    spec = sankey(["A", "B"], [{"source": "A", "target": "B", "value": 5}])
    assert spec.height == 480

