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
