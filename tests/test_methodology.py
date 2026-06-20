from pathlib import Path
import pytest
from pydantic import ValidationError

from myst import AxisOption, MethodologySpace

STUB_PATH = (
    Path(__file__).parent.parent
    / "src/myst/methodology/forest_cover_loss.yaml"
)

def test_loads_from_yaml():
    space = MethodologySpace.from_yaml(STUB_PATH)
    assert space.methodology_space == "forest_cover_loss"
    assert len(space.axes) >= 2

def test_axis_lookup():
    space = MethodologySpace.from_yaml(STUB_PATH)
    axis = space.axis("canopy_cover_threshold_pct")
    assert axis.id == "canopy_cover_threshold_pct"
    assert 10 in axis.option_values()

def test_missing_axes():
    space = MethodologySpace.from_yaml(STUB_PATH)
    with pytest.raises(KeyError):
        space.axis("nonexistent_axis")

def test_grid_size():
    space = MethodologySpace.from_yaml(STUB_PATH)
    expected = 1
    for ax in space.axes:
        expected *= len(ax.options)
    assert space.grid_size() == expected

def test_axis_ids():
    space = MethodologySpace.from_yaml(STUB_PATH)
    ids = space.axis_ids()
    assert "satellite_product" in ids
    assert "canopy_cover_threshold_pct" in ids

def test_option_citation():
    with pytest.raises(ValidationError):
        AxisOption(value = "hansen_gfc", label = "Hansen GFC")