from typing import Any

from .types import Bin, ChartSpec, CrossTab, Ranked


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
    values = [b.percent for b in reversed_bins]

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

    return ChartSpec(option=option, height=height)


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
            "calculable": True,
            "orient": "horizontal",
            "left": "center",
            "bottom": 0,
        }
    else:
        visual_map = {
            "min": 0,
            "max": 100,
            "calculable": True,
            "orient": "horizontal",
            "left": "center",
            "bottom": 0,
        }

    option: dict[str, Any] = {
        "grid": {"left": 200, "right": 40, "top": 40, "bottom": 80},
        "xAxis": {"type": "category", "data": table.x_labels, "splitArea": {"show": True}},
        "yAxis": {"type": "category", "data": table.y_labels, "splitArea": {"show": True}},
        "visualMap": visual_map,
        "series": [{
            "type": "heatmap",
            "data": data,
            "label": {"show": False},
        }],
    }
    if title is not None:
        option["title"] = {"text": title, "left": "left"}

    return ChartSpec(option=option, height=height)


def ranking_bar(
    ranked: list[Ranked],
    *,
    title: str | None = None,
    height: int | None = None,
) -> ChartSpec:
    """Render a ranking bar chart. Uses different label formatters depending on
    whether values are avg-rank floats or top-N counts."""
    reversed_items = list(reversed(ranked))
    labels = [r.label for r in reversed_items]
    values = [r.value for r in reversed_items]

    formatter = "{c}"

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
        "series": [{
            "type": "bar",
            "data": values,
            "label": {"show": True, "position": "right", "formatter": formatter},
            "barWidth": 16,
            "itemStyle": {"borderRadius": 4},
        }],
    }
    if title is not None:
        option["title"] = {"text": title, "left": "left"}

    return ChartSpec(option=option, height=height)
