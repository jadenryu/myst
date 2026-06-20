"""the compiler takes the proposed pins and validates them on the MethodologySpace. axis ids must match, if not, axes 
are gridded rather than pinned. pinned axes must have source evidence and must contain a value that is in an instantiated axis_option"""

from datetime import datetime, timezone
from pydantic import BaseModel

from myst.claim import Claim
from myst.compiler.extractor import Extractor, ProposedPins
from myst.compiler.specs import AxisAssignment, PipelineSpecs
from myst.methodology import MethodologySpace

def compile_claim(claim: Claim, methodology_space: MethodologySpace, extractor: Extractor) -> PipelineSpecs:
    proposed_pins: dict[str, ProposedPins] = {
        pin.axis_id: pin for pin in extractor.extract(claim, methodology_space)
    }
    assignments: list[AxisAssignment] = []
    for a in methodology_space.axes:
        proposed = proposed_pins.get(a.id)
        valid_values = a.option_values()
        if proposed is not None and proposed.value in valid_values: 
            assignments.append(
                AxisAssignment(
                    axis_id = a.id, status = "pinned", values = [proposed.value], source_evidence = proposed.source_evidence
                )
            )
        else: 
            assignments.append(
                AxisAssignment(
                    axis_id = a.id, status = "gridded", values = valid_values
                )
            )
    return PipelineSpecs(
        claim = claim, methodology_space_v = methodology_space.version, assignments = assignments, compiled_at = datetime.now(timezone.utc), compiled_id = extractor.id
    )
