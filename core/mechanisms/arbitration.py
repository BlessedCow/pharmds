from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.mechanisms.candidates import (
    CANDIDATE_ENZYME_INDUCTION,
    CANDIDATE_ENZYME_INHIBITION,
    CANDIDATE_PD_SHARED_EFFECT,
    CANDIDATE_TRANSPORTER_INDUCTION,
    CANDIDATE_TRANSPORTER_INHIBITION,
    InteractionCandidate,
)

CONCERN_EXPOSURE_INCREASE = "exposure_increase"
CONCERN_EXPOSURE_DECREASE = "exposure_decrease"
CONCERN_ADDITIVE_PD_EFFECT = "additive_pd_effect"
CONCERN_UNKNOWN = "unknown"

CONFIDENCE_PLACEHOLDER = "unscored"
SEVERITY_PLACEHOLDER = "unscored"


@dataclass(frozen=True)
class ArbitrationResult:
    """Structured arbitration scaffold for an interaction candidate.

    This is not yet a final clinical rule hit.

    Attributes:
        candidate_type: Source candidate type.
        concern: General interaction concern category.
        precipitant_drug: Drug causing the mechanism/effect.
        object_drug: Drug affected by the mechanism/effect.
        target: Enzyme/transporter target when applicable.
        effect_id: PD effect id when applicable.
        confidence: Placeholder for future evidence/confidence scoring.
        severity: Placeholder for future severity synthesis.
        explanation: Human-readable explanation inherited from the candidate.
         metadata: Optional structured data inherited from the candidate.
    """

    candidate_type: str
    concern: str
    precipitant_drug: str
    object_drug: str
    target: str | None = None
    effect_id: str | None = None
    confidence: str = CONFIDENCE_PLACEHOLDER
    severity: str = SEVERITY_PLACEHOLDER
    explanation: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def key(self) -> tuple[str, str, str, str | None, str | None]:
        """Stable dedupe key."""
        return (
            self.candidate_type,
            self.precipitant_drug,
            self.object_drug,
            self.target,
            self.effect_id,
        )


def arbitrate_candidates(
    candidates: list[InteractionCandidate],
) -> list[ArbitrationResult]:
    """Convert interaction candidates into arbitration scaffold results."""
    results = [
        candidate_to_arbitration_result(candidate)
        for candidate in candidates
    ]

    return dedupe_arbitration_results(results)


def candidate_to_arbitration_result(
    candidate: InteractionCandidate,
) -> ArbitrationResult:
    """Convert one InteractionCandidate into an ArbitrationResult."""
    return ArbitrationResult(
        candidate_type=candidate.candidate_type,
        concern=_concern_for_candidate_type(candidate.candidate_type),
        precipitant_drug=candidate.precipitant_drug,
        object_drug=candidate.object_drug,
        target=candidate.target,
        effect_id=candidate.effect_id,
        explanation=candidate.explanation,
        metadata=candidate.metadata,
    )


def _concern_for_candidate_type(candidate_type: str) -> str:
    if candidate_type in {
        CANDIDATE_ENZYME_INHIBITION,
        CANDIDATE_TRANSPORTER_INHIBITION,
    }:
        return CONCERN_EXPOSURE_INCREASE

    if candidate_type in {
        CANDIDATE_ENZYME_INDUCTION,
        CANDIDATE_TRANSPORTER_INDUCTION,
    }:
        return CONCERN_EXPOSURE_DECREASE

    if candidate_type == CANDIDATE_PD_SHARED_EFFECT:
        return CONCERN_ADDITIVE_PD_EFFECT

    return CONCERN_UNKNOWN


def dedupe_arbitration_results(
    results: list[ArbitrationResult],
) -> list[ArbitrationResult]:
    """Deduplicate arbitration results while preserving first-seen order."""
    seen: set[tuple[str, str, str, str | None, str | None]] = set()
    out: list[ArbitrationResult] = []

    for result in results:
        if result.key in seen:
            continue
        seen.add(result.key)
        out.append(result)

    return out
