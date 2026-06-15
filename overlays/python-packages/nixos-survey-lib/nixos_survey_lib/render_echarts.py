import math
from typing import Any

from .types import Bin, ChartSpec, CrossTab, RankDistribution, Ranked


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

    option: dict[str, Any] = {
        "grid": {"left": 200, "right": 80, "top": 40, "bottom": 30},
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
        option["title"] = {"text": title, "left": "left"}

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
            data.append([xi, yi, value])
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

    option: dict[str, Any] = {
        "grid": {"left": 200, "right": 80, "top": 40, "bottom": 70},
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
        option["title"] = {"text": title, "left": "left"}

    return ChartSpec(
        option=option,
        height=height if height is not None else _default_heatmap_height(len(table.x_labels), len(table.y_labels)),
    )


# Color ramps for diverging_bar. Positive (severity-OK) stacks right in blue;
# the first positive label gets the strongest shade. Negative (severity-bad)
# stacks left in orange; lightest shade first (mildest severity gets lightest
# orange, most severe gets darkest orange).
_DIVERGING_POSITIVE_COLORS = [
    _PALETTE_HEX["blue_default"],
    _PALETTE_HEX["blue_65"],
    _PALETTE_HEX["blue_75"],
    _PALETTE_HEX["blue_85"],
]
_DIVERGING_NEGATIVE_COLORS = [
    _PALETTE_HEX["orange_75"],
    _PALETTE_HEX["orange_65"],
    _PALETTE_HEX["orange_55"],
    _PALETTE_HEX["orange_45"],
]


def diverging_bar(
    bins: list[Bin],
    *,
    positive: list[str],
    negative: list[str],
    neutral: list[str],
    title: str | None = None,
    height: int | None = None,
) -> ChartSpec:
    """Diverging stacked bar: one centered "Severity" spine (negative labels
    stack left in orange, positive stack right in blue) plus a SEPARATE small
    gray "Other" bar for the neutral labels. Colors are hex literals.

    Each category in ``positive``/``negative``/``neutral`` becomes one stacked
    ECharts series; values come from each label's ``Bin.percent``. Negative
    labels are negated so they extend left from zero. Neutral labels render on
    a second y-category ("Other") only.
    """
    pct = {b.label: round(b.percent, 1) for b in bins}

    y_data = ["Other", "Severity"]  # bottom-up: "Severity" renders on top
    series: list[dict[str, Any]] = []

    for i, label in enumerate(positive):
        color = _DIVERGING_POSITIVE_COLORS[min(i, len(_DIVERGING_POSITIVE_COLORS) - 1)]
        series.append({
            "name": label,
            "type": "bar",
            "stack": "severity",
            "data": [0, pct.get(label, 0.0)],
            "itemStyle": {"color": color},
            "label": {"show": True, "formatter": "{c}%"},
        })
    for i, label in enumerate(negative):
        color = _DIVERGING_NEGATIVE_COLORS[min(i, len(_DIVERGING_NEGATIVE_COLORS) - 1)]
        series.append({
            "name": label,
            "type": "bar",
            "stack": "severity",
            "data": [0, -pct.get(label, 0.0)],
            "itemStyle": {"color": color},
            "label": {"show": True, "formatter": "{c}%"},
        })
    for label in neutral:
        series.append({
            "name": label,
            "type": "bar",
            "stack": "neutral",
            "data": [pct.get(label, 0.0), 0],
            "itemStyle": {"color": _PALETTE_HEX["gray_dark"]},
            "label": {"show": True, "formatter": "{c}%"},
        })

    option: dict[str, Any] = {
        "grid": {"left": 80, "right": 80, "top": 40, "bottom": 30},
        "legend": {"top": 0, "type": "scroll"},
        "tooltip": {"trigger": "item", "formatter": "{a}: {c}%"},
        "xAxis": {"type": "value", "axisLabel": {"formatter": "{value}%"}},
        "yAxis": {"type": "category", "data": y_data},
        "series": series,
    }
    if title is not None:
        option["title"] = {"text": title, "left": "left"}

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

    option: dict[str, Any] = {
        "grid": {"left": 60, "right": 40, "top": 40, "bottom": 60},
        "legend": {"top": 0, "type": "scroll"},
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
        option["title"] = {"text": title, "left": "left"}

    return ChartSpec(option=option, height=height if height is not None else 360)


def slope_chart(
    table: CrossTab,
    *,
    title: str | None = None,
    height: int | None = None,
) -> ChartSpec:
    """Two-point slope chart: first vs last x_label column, one line per
    y_label, labeled at both ends. No explicit color (inherits theme palette)."""
    unit = "×" if table.cell_kind == "lift" else "%"
    first_i = 0
    last_i = len(table.x_labels) - 1 if table.x_labels else 0
    x_data = [table.x_labels[first_i], table.x_labels[last_i]] if table.x_labels else []

    series: list[dict[str, Any]] = []
    for yi, y_label in enumerate(table.y_labels):
        start = round(table.cells[first_i][yi], 1)
        end = round(table.cells[last_i][yi], 1)
        series.append({
            "name": y_label,
            "type": "line",
            "data": [start, end],
            "smooth": False,
            "label": {"show": True, "formatter": "{c}" + unit},
        })

    option: dict[str, Any] = {
        "grid": {"left": 60, "right": 120, "top": 40, "bottom": 40},
        "legend": {"top": 0, "type": "scroll"},
        "tooltip": {"trigger": "item", "formatter": "{a}: {c}" + unit},
        "xAxis": {"type": "category", "data": x_data, "boundaryGap": True},
        "yAxis": {"type": "value", "axisLabel": {"formatter": "{value}" + unit}},
        "series": series,
    }
    if title is not None:
        option["title"] = {"text": title, "left": "left"}

    return ChartSpec(option=option, height=height if height is not None else 420)


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

    option: dict[str, Any] = {
        "grid": {"left": 200, "right": 80, "top": 40, "bottom": 30},
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
            "type": "pictorialBar",
            "data": values,
            "symbol": "circle",
            "symbolPosition": "end",
            "symbolSize": 14,
            "barWidth": 4,
            "label": {"show": True, "position": "right", "formatter": "{c}%"},
        }],
    }
    if title is not None:
        option["title"] = {"text": title, "left": "left"}

    return ChartSpec(option=option, height=height if height is not None else _default_bar_height(len(bins)))


# Sequential blue ramp for rank-distribution segments: rank 1 (top) is darkest.
# Index 0 = top rank/band; later segments lighten. The "Unranked" tail segment
# always uses gray (handled separately, not from this ramp).
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
    series: list[dict[str, Any]] = []
    for si, seg_label in enumerate(dist.segment_labels):
        is_last = si == n_segments - 1
        if is_last:
            color = _PALETTE_HEX["gray_light"]
        else:
            color = _RANK_DIST_BLUES[min(si, len(_RANK_DIST_BLUES) - 1)]
        series.append({
            "name": seg_label,
            "type": "bar",
            "stack": "total",
            "data": [round(it.percents[si], 1) for it in items],
            "itemStyle": {"color": color},
        })

    option: dict[str, Any] = {
        "grid": {"left": 200, "right": 40, "top": 40, "bottom": 30},
        "legend": {"top": 0, "type": "scroll"},
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
        option["title"] = {"text": title, "left": "left"}

    return ChartSpec(
        option=option,
        height=height if height is not None else _default_bar_height(len(dist.items)),
    )


def ranking_bar(
    ranked: list[Ranked],
    *,
    title: str | None = None,
    height: int | None = None,
) -> ChartSpec:
    """Render a ranking bar chart. avg_rank values are rounded to 2 decimals;
    top_n_count values are integers."""
    reversed_items = list(reversed(ranked))
    labels = [r.label for r in reversed_items]
    is_avg_rank = bool(ranked) and ranked[0].method == "avg_rank"
    if is_avg_rank:
        values: list[float | int] = [round(r.value, 2) for r in reversed_items]
    else:
        values = [int(r.value) for r in reversed_items]

    option: dict[str, Any] = {
        "grid": {"left": 200, "right": 80, "top": 40, "bottom": 30},
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
            "formatter": "{b}: {c}",
        },
        "series": [{
            "type": "bar",
            "data": values,
            "label": {"show": True, "position": "right", "formatter": "{c}"},
            "barWidth": 16,
            "itemStyle": {"borderRadius": 4},
        }],
    }
    if title is not None:
        option["title"] = {"text": title, "left": "left"}

    return ChartSpec(option=option, height=height if height is not None else _default_bar_height(len(ranked)))
