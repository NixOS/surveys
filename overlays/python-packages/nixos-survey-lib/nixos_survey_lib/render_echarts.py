from typing import Any

from .types import Bin, ChartSpec, CrossTab, Ranked


_BAR_ROW_PX = 28
_BAR_CHROME_PX = 80


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
) -> ChartSpec:
    """Render a heatmap ECharts option dict from a CrossTab.

    For lift cell_kind, the visualMap is diverging centered at 1.0 (min=0, max=2).
    Otherwise it's a sequential 0-100% gradient.
    """
    data: list[list[float]] = []
    for xi, _ in enumerate(table.x_labels):
        for yi, _ in enumerate(table.y_labels):
            value = table.cells[xi][yi]
            data.append([xi, yi, value])

    if table.cell_kind == "lift":
        visual_map: dict[str, Any] = {
            "min": 0,
            "max": 2,
            "precision": 1,
            "calculable": True,
            "orient": "vertical",
            "right": 10,
            "top": "center",
        }
    else:
        visual_map = {
            "min": 0,
            "max": 100,
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
            "splitArea": {"show": True},
            # Match the bar charts: truncate from the END so the start of the
            # label is visible (ellipsis at the tail).
            "axisLabel": {"width": 180, "overflow": "truncate", "interval": 0},
        },
        "visualMap": visual_map,
        "series": [{
            "type": "heatmap",
            "data": data,
            "label": {"show": False},
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
