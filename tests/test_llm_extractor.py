import json
from pathlib import Path

from myst import Claim, MethodologySpace, compile_claim
from myst.compiler.llm_extractor import LLMExtractor

SPACE_PATH = (
    Path(__file__).parent.parent
    / "src/myst/methodology/forest_cover_loss.yaml"
)

class FakeResponse:
    def __init__(self, content: str):
        self._content = content
    def raise_for_status(self):
        pass
    def json(self):
        return {"choices": [{"message": {"content": self._content}}]}

class FakeClient:
    def __init__(self, content: str):
        self.content = content
        self.last_payload = None
    def post(self, url, headers = None, json = None):
        self.last_payload = json
        return FakeResponse(self.content)

def make_claim() -> Claim:
    return Claim(
        raw_text = "Per Hansen GFC, the Amazon lost 12% forest cover since 2010",
        claim_type = "forest_cover_loss",
        value = 12.0,
        unit = "percent"
    )

def load_space() -> MethodologySpace:
    return MethodologySpace.from_yaml(SPACE_PATH)

def first_product(space: MethodologySpace) -> str:
    return space.axis("satellite_product").options[0].value


# --- _parse: turning raw model content into ProposedPins ---

def test_parse_valid_pin():
    content = json.dumps(
        {"pins": [{"axis_id": "satellite_product", "value": "hansen_gfc",
                   "source_evidence": "Per Hansen GFC"}]}
    )
    pins = LLMExtractor._parse(content)
    assert len(pins) == 1
    assert pins[0].axis_id == "satellite_product"
    assert pins[0].value == "hansen_gfc"
    assert pins[0].source_evidence == "Per Hansen GFC"

def test_parse_multiple_pins():
    content = json.dumps(
        {"pins": [
            {"axis_id": "satellite_product", "value": "hansen_gfc"},
            {"axis_id": "canopy_cover_threshold_pct", "value": 30},
        ]}
    )
    pins = LLMExtractor._parse(content)
    assert {p.axis_id for p in pins} == {"satellite_product", "canopy_cover_threshold_pct"}
    # numeric values survive the round-trip as numbers, not strings
    threshold = next(p for p in pins if p.axis_id == "canopy_cover_threshold_pct")
    assert threshold.value == 30

def test_parse_strips_json_code_fences():
    inner = json.dumps({"pins": [{"axis_id": "satellite_product", "value": "hansen_gfc"}]})
    content = f"```json\n{inner}\n```"
    pins = LLMExtractor._parse(content)
    assert len(pins) == 1
    assert pins[0].value == "hansen_gfc"

def test_parse_strips_bare_code_fences():
    inner = json.dumps({"pins": [{"axis_id": "satellite_product", "value": "hansen_gfc"}]})
    content = f"```\n{inner}\n```"
    pins = LLMExtractor._parse(content)
    assert len(pins) == 1
    assert pins[0].value == "hansen_gfc"

def test_parse_empty_pins():
    assert LLMExtractor._parse(json.dumps({"pins": []})) == []

def test_parse_invalid_json_returns_empty():
    assert LLMExtractor._parse("not json at all") == []

def test_parse_non_object_returns_empty():
    # a JSON array has no .get("pins"), so it must fail closed
    assert LLMExtractor._parse("[1, 2, 3]") == []

def test_parse_skips_pins_missing_axis_id():
    content = json.dumps(
        {"pins": [
            {"value": "hansen_gfc"},                       # no axis_id -> skipped
            {"axis_id": "satellite_product", "value": "hansen_gfc"},
        ]}
    )
    pins = LLMExtractor._parse(content)
    assert len(pins) == 1
    assert pins[0].axis_id == "satellite_product"

def test_parse_source_evidence_optional():
    content = json.dumps({"pins": [{"axis_id": "satellite_product", "value": "hansen_gfc"}]})
    pins = LLMExtractor._parse(content)
    assert pins[0].source_evidence is None


# --- extract: full path through an injected (fake) HTTP client ---

def test_extract_returns_parsed_pins():
    space = load_space()
    content = json.dumps(
        {"pins": [{"axis_id": "satellite_product", "value": first_product(space)}]}
    )
    extractor = LLMExtractor(api_key = "test", client = FakeClient(content))
    pins = extractor.extract(make_claim(), space)
    assert len(pins) == 1
    assert pins[0].axis_id == "satellite_product"
    assert pins[0].value == first_product(space)

def test_extract_builds_payload():
    space = load_space()
    fake = FakeClient(json.dumps({"pins": []}))
    extractor = LLMExtractor(api_key = "test", model = "test/model", client = fake)
    extractor.extract(make_claim(), space)

    payload = fake.last_payload
    assert payload is not None
    assert payload["model"] == "test/model"
    assert payload["temperature"] == 0
    roles = [m["role"] for m in payload["messages"]]
    assert roles == ["system", "user"]
    # the user message must carry the claim text and the axis brief
    user_msg = payload["messages"][1]["content"]
    assert make_claim().raw_text in user_msg
    for axis_id in space.axis_ids():
        assert axis_id in user_msg

def test_extractor_id_includes_model():
    extractor = LLMExtractor(model = "anthropic/claude-3.5-haiku")
    assert extractor.id == "llm:anthropic/claude-3.5-haiku"


# --- integration: LLMExtractor feeding compile_claim ---

def test_compile_with_llm_extractor_pins_axis():
    space = load_space()
    product = first_product(space)
    content = json.dumps(
        {"pins": [{"axis_id": "satellite_product", "value": product,
                   "source_evidence": "Per Hansen GFC"}]}
    )
    extractor = LLMExtractor(api_key = "test", client = FakeClient(content))
    spec = compile_claim(make_claim(), space, extractor)

    a = spec.check_assignments("satellite_product")
    assert a.status == "pinned"
    assert a.values == [product]
    assert spec.compiled_id == extractor.id

def test_compile_with_llm_invalid_value_is_gridded():
    space = load_space()
    content = json.dumps(
        {"pins": [{"axis_id": "satellite_product", "value": "not_a_real_product"}]}
    )
    extractor = LLMExtractor(api_key = "test", client = FakeClient(content))
    spec = compile_claim(make_claim(), space, extractor)

    a = spec.check_assignments("satellite_product")
    assert a.status == "gridded"

def test_compile_with_empty_extraction_grids_everything():
    space = load_space()
    extractor = LLMExtractor(api_key = "test", client = FakeClient(json.dumps({"pins": []})))
    spec = compile_claim(make_claim(), space, extractor)

    assert all(a.status == "gridded" for a in spec.assignments)
    assert spec.grid_size() == space.grid_size()
