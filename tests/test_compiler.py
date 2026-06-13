from pathlib import Path

import pytest 
from pydantic import ValidationError

from lurq import AxisAssignment, Claim, compile_claim, Extractor, ManualExtractor, MethodologySpace


SPACE_PATH = (
    Path(__file__).parent.parent
    / "src/lurq/methodology/forest_cover_loss.yaml"
)

def make_claim() -> Claim:
    return Claim(
        raw_text = f"The Amazon lost 12% of its forest cover since 2010, per Hansen GFC", claim_type = "forest_cover_loss", value = 12.0, unit = "percent"
    )

def test_compile_w_no_pins():
    space = MethodologySpace.from_yaml(SPACE_PATH)
    spec = compile_claim(make_claim(), space, ManualExtractor())

    assert len(spec.assignments) == len(space.axes)
    assert all(a.status == "gridded" for a in spec.assignments)
    assert spec.grid_size() == space.grid_size()

def test_compile_pin():
    space = MethodologySpace.from_yaml(SPACE_PATH)
    first_product = space.axis("satellite_product").options[0].value

    extractor = ManualExtractor(
        pins = {"satellite_product": first_product}, 
        source_evidence = {"satelllite_product": "stated in source"}
    )
    spec = compile_claim(make_claim(), space, extractor)
    a = spec.assignments("satellite_product")

    assert a.status == "pinned"
    assert a.values == [first_product]
    assert a.source_evidence == "stated in source"

def test_compile_invalid_pin():
    space = MethodologySpace.from_yaml(SPACE_PATH)
    extractor = ManualExtractor(pins = {"satellite_product": "random"}, source_evidence = "random")
    spec = compile_claim(make_claim(), space, extractor)

    a = spec.check_assignments("satellite_product")
    assert a.status == "gridded"

## make sure the versions between the methodology space and the pipelinespecs methodology space is the same
def test_versions():
    space = MethodologySpace.from_yaml(SPACE_PATH)
    spec = compile_claim(make_claim(), space, ManualExtractor())
    assert space.version == spec.methodology_space_v 

def manual_extractor_pinned_version():
    space = MethodologySpace.from_yaml(SPACE_PATH)
    spec = compile_claim(make_claim(), space, ManualExtractor())
    assert spec.compiled_id == "manual"

def test_pinning_reduces_grid_size_by_axis_option(): 
    space = MethodologySpace.from_yaml(SPACE_PATH)
    first_product = space.axis("satellite_product").options[0].value
    n_product_options = len(space.axis("satellite_product").options)

    spec_no_pins = compile_claim(make_claim(), space, ManualExtractor())
    spec_pinned = compile_claim(
        make_claim(), space, ManualExtractor(pins={"satellite_product": first_product})
    )

    assert spec_pinned.grid_size() * n_product_options == spec_no_pins.grid_size()

def test_pinned_value():
    with pytest.raises(ValidationError):
        AxisAssignment(axis_id = "1", status = "pinned", values = [10, 30])
    
