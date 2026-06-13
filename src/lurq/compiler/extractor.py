from pydantic import BaseModel
from typing import Protocol
from lurq.claim import Claim
from lurq.methodology import MethodologySpace

class ProposedPins(BaseModel):
    axis_id: str
    value: str | int | float
    source_evidence: str | None = None

class Extractor(Protocol):
    id: str
    def extract(self, claim: Claim, methodology_space: MethodologySpace) -> list[ProposedPins]: ...


class ManualExtractor:
    id = "manual"
    def __init__(self, pins: dict[str, str | float | int] | None = None, source_evidence: dict[str, str | float | int] | None = None):
        self.pins = pins or {}
        self.source_evidence = source_evidence or {}
    def extract(self, claim: Claim = None, methodology_space: MethodologySpace = None) -> list[ProposedPins]:
        return [ProposedPins(
            axis_id = axis_id,
            value = value, 
            source_evidence = self.source_evidence.get(axis_id),
        )
        for axis_id, value in self.pins.items()
        ]

