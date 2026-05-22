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