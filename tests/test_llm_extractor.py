import json
from pathlib import Path

from lurq import Claim, MethodologySpace, compile_claim
from lurq.compiler.llm_extractor import LLMExtractor

SPACE_PATH = (
    Path(__file__).parent.parent
    / "src/lurq/methodology/forest_cover_loss.yaml"
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

def first_product(space: MethodologySpace) -> str:
    return space.axis("satellite_product").options[0].value

def test_parse_valid_pin():
    pass