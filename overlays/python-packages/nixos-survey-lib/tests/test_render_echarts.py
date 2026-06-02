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
