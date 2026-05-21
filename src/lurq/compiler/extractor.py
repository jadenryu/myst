from turtle import st
from pydantic import Basemodel
from typing import Literal 

from lurq.claim import Claim
from lurq.methodology import MethodologySpace

class ProposedPin(BaseModel):
    axis_id: str
    value: str | int | float
    source_evidence: str | None = None

class Extractor(Protocol):
    id: str
    ## def extract(BaseModel):