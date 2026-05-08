"""Confidence scoring scaffold for policy concern results.

This module assigns preliminary confidence labels to policy results.

It intentionally does not assign final clinical severity or recommendations.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.mechanism_candidates import (
    CANDIDATE_ENZYME_INDUCTION,
    CANDIDATE_ENZYME_INHIBITION,
    CANDIDATE_PD_SHARED_EFFECT,
    CANDIDATE_TRANSPORTER_INDUCTION,
    CANDIDATE_TRANSPORTER_INHIBITION,
)
from core.mechanism_policy import (
    POLICY_EXPOSURE_REDUCTION_CONCERN,
    POLICY_MECHANISTIC_CONCERN,
    POLICY_SAFETY_CONCERN,
    POLICY_TOLERABILITY_CONCERN,
    ConcernPolicyResult,
)

CONFIDENCE_LOW = "low"
CONFIDENCE_MODERATE = "moderate"
CONFIDENCE_HIGH = "high"
SEVERITY_UNSCORED = "unscored"


@dataclass(frozen=True)
class ScoredConcern:
    """Policy concern with preliminary confidence scoring.

    This is still not a final clinical rule hit.
    """

    policy_concern: str
    source_concern: str
    precipitant_drug: str
    object_drug: str
    target: str | None = None
    effect_id: str | None = None
    candidate_type: str | None = None
    confidence: str = CONFIDENCE_LOW
    severity: str = SEVERITY_UNSCORED
    explanation: str = ""

    @property
    def key(self) -> tuple[str, str, str, str | None, str | None]:
        """Stable dedupe key."""
        return (
            self.policy_concern,
            self.precipitant_drug,
            self.object_drug,
            self.target,
            self.effect_id,
        )


def score_policy_results(
    results: list[ConcernPolicyResult],
) -> list[ScoredConcern]:
    """Score policy results with preliminary confidence labels."""
    scored = [
        policy_result_to_scored_concern(result)
        for result in results
    ]

    return dedupe_scored_concerns(scored)


def policy_result_to_scored_concern(
    result: ConcernPolicyResult,
) -> ScoredConcern:
    """Convert one policy result into a scored concern."""
    return ScoredConcern(
        policy_concern=result.policy_concern,
        source_concern=result.source_concern,
        precipitant_drug=result.precipitant_drug,
        object_drug=result.object_drug,
        target=result.target,
        effect_id=result.effect_id,
        candidate_type=result.candidate_type,
        confidence=_confidence_for_policy_result(result),
        severity=SEVERITY_UNSCORED,
        explanation=result.explanation,
    )


def _confidence_for_policy_result(result: ConcernPolicyResult) -> str:
    if result.candidate_type in {
        CANDIDATE_ENZYME_INHIBITION,
        CANDIDATE_ENZYME_INDUCTION,
        CANDIDATE_TRANSPORTER_INHIBITION,
        CANDIDATE_TRANSPORTER_INDUCTION,
    }:
        return CONFIDENCE_HIGH

    if result.candidate_type == CANDIDATE_PD_SHARED_EFFECT:
        if result.policy_concern == POLICY_SAFETY_CONCERN:
            return CONFIDENCE_HIGH
        if result.policy_concern == POLICY_TOLERABILITY_CONCERN:
            return CONFIDENCE_MODERATE

    if result.policy_concern in {
        POLICY_MECHANISTIC_CONCERN,
        POLICY_EXPOSURE_REDUCTION_CONCERN,
    }:
        return CONFIDENCE_MODERATE

    return CONFIDENCE_LOW


def dedupe_scored_concerns(
    concerns: list[ScoredConcern],
) -> list[ScoredConcern]:
    """Deduplicate scored concerns while preserving first-seen order."""
    seen: set[tuple[str, str, str, str | None, str | None]] = set()
    out: list[ScoredConcern] = []

    for concern in concerns:
        if concern.key in seen:
            continue
        seen.add(concern.key)
        out.append(concern)

    return out