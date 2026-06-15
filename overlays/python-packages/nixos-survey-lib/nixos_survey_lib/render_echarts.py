import math
from typing import Any

from .types import Bin, ChartSpec, Combination, CrossTab, RankDistribution


_BAR_ROW_PX = 28
_BAR_CHROME_PX = 80

# Hex literals pre-resolved from the @nixos/branding oklch tokens (the frontend
# only resolves oklch->hex for the theme PALETTE and heatmap gradients, never for
# arbitrary series colors). diverging_bar and rank_distribution_bar emit these
# directly. afghani-blue DEFAULT (#4d6fb7) matches the branding's documented hex.
_PALETTE_HEX = {
    "blue_default": "#4d6fb7",
    "blue_25": "#15213a",
    "blue_35": "#28395f",
    "blue_45": "#3b5487",
    "blue_65": "#698dd8",
    "blue_75": "#87adfa",
    "blue_85": "#b7cefd",
    "orange_45": "#7b461f",
    "orange_55": "#a25e2c",
    "orange_65": "#c77942",
    "orange_75": "#e99861",
    "gray_dark": "#717171",
    "gray_light": "#aeaeae",
}


def _default_bar_height(n_bars: int) -> int:
    """Pick a chart height that grows with the number of bars so wide charts
    don't get squeezed. ~28px per bar plus chrome for title, padding, grid."""
    return max(240, n_bars * _BAR_ROW_PX + _BAR_CHROME_PX)


def horizontal_bar(
    bins: list[Bin],
    *,
    title: str | None = None,
    height: int | None = None,
) -> ChartSpec:
    """Render a horizontal-bar ECharts option dict from a list of Bin.

    The y-axis is reversed so the largest bar sits at the top.
    """
    reversed_bins = list(reversed(bins))
    labels = [b.label for b in reversed_bins]
    values = [round(b.percent, 1) for b in reversed_bins]

    grid_top = 64 if title is not None else 40
    option: dict[str, Any] = {
        "grid": {"left": 200, "right": 80, "top": grid_top, "bottom": 30},
        "xAxis": {"type": "value", "show": False, "max": "dataMax"},
        "yAxis": {
            "type": "category",
            "data": labels,
            "axisLabel": {"width": 180, "overflow": "truncate"},
            "axisLine": {"show": False},
            "axisTick": {"show": False},
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "shadow"},
            "formatter": "{b}: {c}%",
        },
        "series": [{
            "type": "bar",
            "data": values,
            "label": {"show": True, "position": "right", "formatter": "{c}%"},
            "barWidth": 16,
            "itemStyle": {"borderRadius": 4},
        }],
    }
    if title is not None:
        option["title"] = {"text": title, "left": "left", "top": 0}

    return ChartSpec(option=option, height=height if height is not None else _default_bar_height(len(bins)))


def _default_heatmap_height(x_count: int, y_count: int) -> int:
    """Pick a heatmap container height that produces roughly-square cells
    given a typical effective grid width (~560px after left/right padding)."""
    grid_width = 560
    target_cell_h = max(36, grid_width // max(x_count, 1))
    chrome = 40 + 80  # top + bottom grid padding plus visualMap room
    return chrome + target_cell_h * y_count


def heatmap(
    table: CrossTab,
    *,
    title: str | None = None,
    height: int | None = None,
    vm_min: float | None = None,
    vm_max: float | None = None,
    annotate: bool = False,
) -> ChartSpec:
    """Render a heatmap ECharts option dict from a CrossTab.

    For lift cell_kind, the visualMap defaults to diverging centered at 1.0
    (min=0, max=2). Otherwise it's a sequential gradient that, when vm_min
    and/or vm_max are unspecified, auto-scales to the data's actual range
    (rounded to the nearest 10) so the full palette is used.

    Pass ``vm_min=0, vm_max=100`` to force a fixed 0-100 percent scale (e.g.,
    when comparing several percent heatmaps and you want their colors to mean
    the same thing across charts).
    """
    data: list[list[float]] = []
    cell_values: list[float] = []
    for xi, _ in enumerate(table.x_labels):
        for yi, _ in enumerate(table.y_labels):
            value = table.cells[xi][yi]
            data.append([xi, yi, round(value, 1)])
            cell_values.append(value)

    if table.cell_kind == "lift":
        resolved_min = vm_min if vm_min is not None else 0
        resolved_max = vm_max if vm_max is not None else 2
        visual_map: dict[str, Any] = {
            "min": resolved_min,
            "max": resolved_max,
            "precision": 1,
            "calculable": True,
            "orient": "vertical",
            "right": 10,
            "top": "center",
        }
    else:
        # Percent (rate / composition): auto-scale to data range when not
        # explicitly bounded. Round min down and max up to the nearest 10 for
        # readable legend tick marks.
        if vm_min is None:
            data_min = min(cell_values) if cell_values else 0
            resolved_min = max(0, math.floor(data_min / 10) * 10)
        else:
            resolved_min = vm_min
        if vm_max is None:
            data_max = max(cell_values) if cell_values else 100
            resolved_max = min(100, math.ceil(data_max / 10) * 10)
        else:
            resolved_max = vm_max
        visual_map = {
            "min": resolved_min,
            "max": resolved_max,
            "calculable": True,
            "orient": "vertical",
            "right": 10,
            "top": "center",
        }

    grid_top = 64 if title is not None else 40
    option: dict[str, Any] = {
        "grid": {"left": 200, "right": 80, "top": grid_top, "bottom": 70},
        "xAxis": {
            "type": "category",
            "data": table.x_labels,
            "splitArea": {"show": True},
            # interval=0 forces every label to render even if they'd overlap;
            # rotate makes long labels (e.g. "Less than 1 year") fit horizontally.
            "axisLabel": {"interval": 0, "rotate": 30},
        },
        "yAxis": {
            "type": "category",
            "data": table.y_labels,
            # ECharts category y-axis defaults to bottom-up (index 0 at bottom);
            # invert so the first item is at the top (natural reading order).
            "inverse": True,
            "splitArea": {"show": True},
            # Match the bar charts: truncate from the END so the start of the
            # label is visible (ellipsis at the tail).
            "axisLabel": {"width": 180, "overflow": "truncate", "interval": 0},
        },
        "visualMap": visual_map,
        "series": [{
            "type": "heatmap",
            "data": data,
            "label": (
                {
                    "show": True,
                    "formatter": "{@[2]}×" if table.cell_kind == "lift" else "{@[2]}%",
                }
                if annotate
                else {"show": False}
            ),
            "emphasis": {
                "itemStyle": {
                    "shadowBlur": 10,
                    "shadowColor": "rgba(0,0,0,0.5)",
                },
            },
        }],
    }
    if title is not None:
        option["title"] = {"text": title, "left": "left", "top": 0}

    return ChartSpec(
        option=option,
        height=height if height is not None else _default_heatmap_height(len(table.x_labels), len(table.y_labels)),
    )


# Color ramps for likert_bar.
# Positive (agreement) labels use blue shades: darkest = most positive.
_LIKERT_POSITIVE_COLORS = [
    _PALETTE_HEX["blue_default"],
    _PALETTE_HEX["blue_75"],
]
# Negative (disagreement) labels use orange shades: lightest = mildest → darkest = worst.
# Three distinct shades so 3-category negative scales never repeat a color.
_LIKERT_NEGATIVE_COLORS = [
    _PALETTE_HEX["orange_75"],
    _PALETTE_HEX["orange_55"],
    _PALETTE_HEX["orange_45"],
]
# Neutral labels use two distinct grays.
_LIKERT_NEUTRAL_COLORS = [
    _PALETTE_HEX["gray_light"],
    _PALETTE_HEX["gray_dark"],
]


def likert_bar(
    bins: list[Bin],
    *,
    positive: list[str],
    negative: list[str],
    neutral: list[str],
    order: list[str] | None = None,
    title: str | None = None,
    height: int | None = None,
) -> ChartSpec:
    """100%-stacked horizontal bar for Likert-scale data. One bar; each label
    becomes one stacked ``bar`` series sharing ``stack: "likert"``.

    Segment order left→right: positive labels (blue shades, darkest first),
    then negative labels (orange shades), then neutral labels (distinct grays).
    All values are positive percents. Colors are hex literals.
    """
    pct = {b.label: round(b.percent, 1) for b in bins}
    series: list[dict[str, Any]] = []

    for i, label in enumerate(positive):
        color = _LIKERT_POSITIVE_COLORS[min(i, len(_LIKERT_POSITIVE_COLORS) - 1)]
        series.append({
            "name": label,
            "type": "bar",
            "stack": "likert",
            "data": [pct.get(label, 0.0)],
            "itemStyle": {"color": color},
            "label": {"show": True, "formatter": "{c}%"},
        })
    for i, label in enumerate(negative):
        color = _LIKERT_NEGATIVE_COLORS[min(i, len(_LIKERT_NEGATIVE_COLORS) - 1)]
        series.append({
            "name": label,
            "type": "bar",
            "stack": "likert",
            "data": [pct.get(label, 0.0)],
            "itemStyle": {"color": color},
            "label": {"show": True, "formatter": "{c}%"},
        })
    for i, label in enumerate(neutral):
        color = _LIKERT_NEUTRAL_COLORS[min(i, len(_LIKERT_NEUTRAL_COLORS) - 1)]
        series.append({
            "name": label,
            "type": "bar",
            "stack": "likert",
            "data": [pct.get(label, 0.0)],
            "itemStyle": {"color": color},
            "label": {"show": True, "formatter": "{c}%"},
        })

    legend_top = 28 if title is not None else 0
    grid_top = 64 if title is not None else 40
    option: dict[str, Any] = {
        "grid": {"left": 80, "right": 80, "top": grid_top, "bottom": 30},
        "legend": {"top": legend_top},
        "tooltip": {"trigger": "item", "formatter": "{a}: {c}%"},
        "xAxis": {"type": "value", "max": 100, "axisLabel": {"formatter": "{value}%"}},
        "yAxis": {"type": "category", "data": [""]},
        "series": series,
    }
    if title is not None:
        option["title"] = {"text": title, "left": "left", "top": 0}

    return ChartSpec(option=option, height=height if height is not None else 200)


def line_chart(
    table: CrossTab,
    *,
    title: str | None = None,
    height: int | None = None,
) -> ChartSpec:
    """One line series per y_label over the x_labels axis. Cell values are
    cells[xi][yi]. Emits no explicit color (inherits the theme palette)."""
    unit = "×" if table.cell_kind == "lift" else "%"
    series: list[dict[str, Any]] = []
    for yi, y_label in enumerate(table.y_labels):
        values = [round(table.cells[xi][yi], 1) for xi in range(len(table.x_labels))]
        series.append({
            "name": y_label,
            "type": "line",
            "data": values,
            "smooth": False,
        })

    legend_top = 28 if title is not None else 0
    grid_top = 64 if title is not None else 40
    option: dict[str, Any] = {
        "grid": {"left": 60, "right": 40, "top": grid_top, "bottom": 60},
        "legend": {"top": legend_top},
        "tooltip": {"trigger": "axis"},
        "xAxis": {
            "type": "category",
            "data": table.x_labels,
            "axisLabel": {"interval": 0, "rotate": 30},
        },
        "yAxis": {"type": "value", "axisLabel": {"formatter": "{value}" + unit}},
        "series": series,
    }
    if title is not None:
        option["title"] = {"text": title, "left": "left", "top": 0}

    return ChartSpec(option=option, height=height if height is not None else 360)



def lollipop(
    bins: list[Bin],
    *,
    title: str | None = None,
    height: int | None = None,
) -> ChartSpec:
    """Horizontal lollipop: a pictorialBar series whose stem is the bar body and
    whose dot (circle, at the end) marks the value. Largest sits at the top.
    No explicit color (inherits theme palette)."""
    reversed_bins = list(reversed(bins))
    labels = [b.label for b in reversed_bins]
    values = [round(b.percent, 1) for b in reversed_bins]

    grid_top = 64 if title is not None else 40
    option: dict[str, Any] = {
        "grid": {"left": 200, "right": 80, "top": grid_top, "bottom": 30},
        "xAxis": {"type": "value", "show": False, "max": "dataMax"},
        "yAxis": {
            "type": "category",
            "data": labels,
            "axisLabel": {"width": 180, "overflow": "truncate"},
            "axisLine": {"show": False},
            "axisTick": {"show": False},
        },
        "tooltip": {
            "trigger": "item",
            "formatter": "{b}: {c}%",
        },
        "series": [
            {
                "type": "bar",
                "data": values,
                "barWidth": 2,
                "itemStyle": {"color": _PALETTE_HEX["blue_default"]},
                "silent": True,
            },
            {
                "type": "pictorialBar",
                "data": values,
                "symbol": "circle",
                "symbolPosition": "end",
                "symbolSize": 14,
                "itemStyle": {"color": _PALETTE_HEX["blue_default"]},
                "label": {"show": True, "position": "right", "formatter": "{c}%"},
            },
        ],
    }
    if title is not None:
        option["title"] = {"text": title, "left": "left", "top": 0}

    return ChartSpec(option=option, height=height if height is not None else _default_bar_height(len(bins)))


# Sequential blue ramp for rank-distribution segments: monotonically dark→light.
# Index 0 = darkest (rank 1); later indices lighten strictly.
# 7 shades give good even-spacing for any N from 1 to 7.
# The "Unranked" tail segment always uses gray_light (#aeaeae), separate from this ramp.
_RANK_DIST_BLUES = [
    _PALETTE_HEX["blue_25"],
    _PALETTE_HEX["blue_35"],
    _PALETTE_HEX["blue_45"],
    _PALETTE_HEX["blue_default"],
    _PALETTE_HEX["blue_65"],
    _PALETTE_HEX["blue_75"],
    _PALETTE_HEX["blue_85"],
]


def rank_distribution_bar(
    dist: RankDistribution,
    *,
    bands: list[tuple[int, int]] | None = None,
    title: str | None = None,
    height: int | None = None,
) -> ChartSpec:
    """100%-stacked horizontal bar from a RankDistribution. One series per
    segment; top rank/band = darkest blue, lighter for later segments, gray for
    the trailing "Unranked" segment. Colors are hex literals. ``bands`` is
    accepted for signature parity (the segment structure already comes from
    ``dist.segment_labels``) and otherwise unused.
    """
    # ECharts category y-axis is bottom-up; reverse so the first (top-share)
    # item appears at the top.
    items = list(reversed(dist.items))
    labels = [it.label for it in items]

    n_segments = len(dist.segment_labels)
    # Number of ranked (non-Unranked) segments is n_segments - 1 when there is
    # an Unranked tail; we treat the last segment as Unranked (gray) always.
    n_ranked = n_segments - 1 if n_segments > 0 else 0
    series: list[dict[str, Any]] = []
    for si, seg_label in enumerate(dist.segment_labels):
        is_last = si == n_segments - 1
        if is_last:
            color = _PALETTE_HEX["gray_light"]
        else:
            # Even spacing across the ramp so rank 1 = darkest, rank N = lightest,
            # with uniform perceptual distance regardless of how many ranks there are.
            ramp = _RANK_DIST_BLUES
            idx = round(si * (len(ramp) - 1) / max(n_ranked - 1, 1))
            color = ramp[idx]
        series.append({
            "name": seg_label,
            "type": "bar",
            "stack": "total",
            "data": [round(it.percents[si], 1) for it in items],
            "itemStyle": {"color": color},
        })

    legend_top = 28 if title is not None else 0
    grid_top = 64 if title is not None else 40
    option: dict[str, Any] = {
        "grid": {"left": 200, "right": 40, "top": grid_top, "bottom": 30},
        "legend": {"top": legend_top},
        "tooltip": {"trigger": "item", "formatter": "{a} — {b}: {c}%"},
        "xAxis": {"type": "value", "max": 100, "axisLabel": {"formatter": "{value}%"}},
        "yAxis": {
            "type": "category",
            "data": labels,
            "axisLabel": {"width": 180, "overflow": "truncate"},
            "axisLine": {"show": False},
            "axisTick": {"show": False},
        },
        "series": series,
    }
    if title is not None:
        option["title"] = {"text": title, "left": "left", "top": 0}

    return ChartSpec(
        option=option,
        height=height if height is not None else _default_bar_height(len(dist.items)),
    )


def sankey(
    nodes: list[str],
    links: list[dict[str, Any]],
    *,
    title: str | None = None,
    height: int | None = None,
) -> ChartSpec:
    """Render a Sankey/alluvial ECharts option dict.

    ``nodes`` is a list of node names; ``links`` is a list of
    ``{"source", "target", "value"}`` dicts. No grid/axes and no explicit
    colors — the chart inherits the theme palette. A tooltip is included.
    """
    option: dict[str, Any] = {
        "tooltip": {
            "trigger": "item",
            "triggerOn": "mousemove",
        },
        "series": [{
            "type": "sankey",
            "data": [{"name": n} for n in nodes],
            "links": links,
            "emphasis": {"focus": "adjacency"},
            "lineStyle": {"color": "gradient", "curveness": 0.5},
            "label": {"overflow": "truncate"},
        }],
    }
    if title is not None:
        option["title"] = {"text": title, "left": "left", "top": 0}
    return ChartSpec(option=option, height=height if height is not None else 480)


# Dot-matrix fill colors. Hex literals only — the frontend resolves oklch only
# for the theme PALETTE and heatmap visualMap gradients, not arbitrary series
# colors, so any explicit color here MUST be hex.
_UPSET_DOT_FILLED = "#5277c3"
_UPSET_DOT_FADED = "#c9c9c9"


def upset(
    combos: list[Combination],
    set_totals: list[tuple[str, int]],
    dropped_count: int,
    *,
    height: int,
    set_labels: dict[str, str] | None = None,
) -> ChartSpec:
    """Render an UpSet plot as a multi-grid ECharts option.

    Canonical left-to-right layout: [set-code labels] → [totals bar] →
    [dot-matrix].

    grids: [0] top bar of intersection sizes (aligned with dot-matrix),
    [1] dot-matrix (sets × intersections), [2] left totals bar (per-set
    counts). The dot-matrix shares the intersection category x-axis with the
    top bar and the set category y-axis with the left bar.

    ``set_labels`` maps each full set name to a short display code. When
    provided, the totals-bar y-axis (index 2) shows the short codes; the
    dot-matrix y-axis (index 1) hides its labels so only the codes on the far
    left are visible. Combos and set_totals continue to be keyed on full names
    internally.

    ``dropped_count`` is surfaced in ``title.subtext`` (no silent truncation).
    """
    row_names = [label for label, _total in set_totals]
    totals = [total for _label, total in set_totals]
    n_cols = len(combos)
    col_categories = [str(i) for i in range(n_cols)]

    # Displayed codes for the totals-bar y-axis: short codes when provided,
    # otherwise fall back to the full names.
    def _display_code(name: str) -> str:
        if set_labels is not None:
            return set_labels.get(name, name)
        return name

    display_codes = [_display_code(name) for name in row_names]

    # Fix 1: cap the totals value axis max at ~1.6× the largest total so the
    # left-positioned label on the longest bar stays inside the grid (right of
    # the set-code column) rather than overflowing into it.
    max_total = max(totals) if totals else 1
    totals_axis_max = int(max_total * 1.6) + 1

    # Per-column combo name strings for tooltip names.
    def _combo_name(combo: Combination) -> str:
        codes = " · ".join(_display_code(m) for m in combo.members)
        return f"{codes}: {combo.size}"

    combo_names = [_combo_name(c) for c in combos]

    # Dot-matrix: one point per (column, set row), filled if the set is a
    # member of that column's combination.
    dot_data: list[dict[str, Any]] = []
    for ci, combo in enumerate(combos):
        member_set = set(combo.members)
        for ri, set_label in enumerate(row_names):
            filled = set_label in member_set
            dot_data.append({
                "value": [ci, ri],
                "name": combo_names[ci],
                "itemStyle": {"color": _UPSET_DOT_FILLED if filled else _UPSET_DOT_FADED},
            })

    # Connector lines: one 2-point line series per column spanning the topmost
    # to bottommost filled row. Expressed as a plain `line` series (NOT a
    # `custom`/renderItem series, which cannot survive JSON serialization since
    # renderItem must be a runtime function). Single-/zero-filled columns get
    # no connector. Hex color only (no oklch).
    connector_series: list[dict[str, Any]] = []
    for ci, combo in enumerate(combos):
        member_set = set(combo.members)
        filled_rows = [
            ri for ri, set_label in enumerate(row_names)
            if set_label in member_set
        ]
        if len(filled_rows) < 2:
            continue
        r_min, r_max = min(filled_rows), max(filled_rows)
        connector_series.append({
            "type": "line",
            "xAxisIndex": 1,
            "yAxisIndex": 1,
            "data": [[ci, r_min], [ci, r_max]],
            "symbol": "none",
            "lineStyle": {"color": _UPSET_DOT_FILLED, "width": 2},
            "z": 1,
            "silent": True,
            "tooltip": {"show": False},
        })

    # Top bar data items: objects with value + name for {b} tooltip.
    top_bar_data = [
        {"value": c.size, "name": combo_names[ci]}
        for ci, c in enumerate(combos)
    ]

    # Left totals bar data items: objects with value + name for {b} tooltip.
    left_bar_data = [
        {"value": total, "name": f"{_display_code(name)}: {total}"}
        for name, total in set_totals
    ]

    option: dict[str, Any] = {
        "grid": [
            # 0: top bar (intersection sizes) — same left/right as dot-matrix
            {"left": 190, "right": 40, "top": 50, "height": 110},
            # 1: dot-matrix — right of the totals bar
            {"left": 190, "right": 40, "top": 180, "bottom": 30},
            # 2: left totals bar — narrow column; y-axis carries set codes
            {"left": 70, "width": 90, "top": 180, "bottom": 30},
        ],
        "xAxis": [
            # 0: top bar category (intersection columns), labels hidden
            {
                "type": "category", "data": col_categories, "gridIndex": 0,
                "axisLabel": {"show": False}, "axisTick": {"show": False},
                "axisLine": {"show": False},
            },
            # 1: dot-matrix category (shares the intersection columns)
            {
                "type": "category", "data": col_categories, "gridIndex": 1,
                "axisLabel": {"show": False}, "axisTick": {"show": False},
                "axisLine": {"show": False}, "splitLine": {"show": False},
            },
            # 2: left bar value axis, grows leftward; max capped so the
            # longest bar's label stays inside the grid (fix 1).
            {"type": "value", "gridIndex": 2, "inverse": True, "show": False,
             "max": totals_axis_max},
        ],
        "yAxis": [
            # 0: top bar value axis
            {"type": "value", "gridIndex": 0},
            # 1: dot-matrix set rows — labels hidden; codes live on the
            # totals-bar axis to the left so there is no overlap.
            {
                "type": "category", "data": row_names, "gridIndex": 1,
                "inverse": True, "axisTick": {"show": False},
                "axisLine": {"show": False}, "splitLine": {"show": False},
                "axisLabel": {"show": False},
            },
            # 2: totals-bar set rows (aligned with dot-matrix) — shows short
            # codes (or full names when set_labels is None) on the far left.
            {
                "type": "category", "data": display_codes, "gridIndex": 2,
                "inverse": True, "axisTick": {"show": False},
                "axisLine": {"show": False},
            },
        ],
        "tooltip": {"trigger": "item", "formatter": "{b}"},
        "series": [
            {
                "type": "bar", "xAxisIndex": 0, "yAxisIndex": 0,
                "data": top_bar_data,
                "label": {"show": True, "position": "top", "formatter": "{c}"},
                "barWidth": "60%",
            },
            *connector_series,
            {
                "type": "scatter", "xAxisIndex": 1, "yAxisIndex": 1,
                "data": dot_data,
                "symbolSize": 16,
                "z": 2,
            },
            {
                "type": "bar", "xAxisIndex": 2, "yAxisIndex": 2,
                "data": left_bar_data,
                "label": {"show": True, "position": "left", "formatter": "{c}"},
                "barWidth": "60%",
            },
        ],
    }

    if dropped_count > 0:
        option["title"] = {
            "subtext": f"{dropped_count} combination(s) not shown "
                       f"(below 5 respondents or beyond the display cap).",
            "left": "left",
        }

    return ChartSpec(option=option, height=height)

