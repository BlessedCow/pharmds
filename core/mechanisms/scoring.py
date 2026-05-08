"""Confidence scoring scaffold for policy concern results.

This module assigns preliminary confidence labels to policy results and carries
lightweight aggregate context for future scoring.

It intentionally does not assign final clinical severity or recommendations.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.mechanisms.aggregation import AggregateConcern
from core.mechanisms.candidates import (
    CANDIDATE_ENZYME_INDUCTION,
    CANDIDATE_ENZYME_INHIBITION,
    CANDIDATE_PD_SHARED_EFFECT,
    CANDIDATE_TRANSPORTER_INDUCTION,
    CANDIDATE_TRANSPORTER_INHIBITION,
)
from core.mechanisms.policy import (
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
    aggregate_member_count: int = 0
    related_targets: tuple[str, ...] = ()
    related_effects: tuple[str, ...] = ()
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
    aggregates: list[AggregateConcern] | None = None,
) -> list[ScoredConcern]:
    """Score policy results with preliminary confidence labels."""
    aggregate_list = aggregates or []
    scored = [
        policy_result_to_scored_concern(result, aggregate_list)
        for result in results
    ]

    return dedupe_scored_concerns(scored)


def policy_result_to_scored_concern(
    result: ConcernPolicyResult,
    aggregates: list[AggregateConcern] | None = None,
) -> ScoredConcern:
    """Convert one policy result into a scored concern."""
    aggregate_context = _aggregate_context_for_result(result, aggregates or [])

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
        aggregate_member_count=aggregate_context["member_count"],
        related_targets=aggregate_context["targets"],
        related_effects=aggregate_context["effects"],
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


def _aggregate_context_for_result(
    result: ConcernPolicyResult,
    aggregates: list[AggregateConcern],
) -> dict[str, tuple[str, ...] | int]:
    matching = [
        aggregate
        for aggregate in aggregates
        if _aggregate_matches_result(aggregate, result)
    ]

    if not matching:
        return {
            "member_count": 0,
            "targets": (),
            "effects": (),
        }

    member_count = max(len(aggregate.members) for aggregate in matching)
    targets = _unique_sorted(
        target
        for aggregate in matching
        for target in aggregate.targets
    )
    effects = _unique_sorted(
        aggregate.effect_id
        for aggregate in matching
        if aggregate.effect_id
    )

    return {
        "member_count": member_count,
        "targets": targets,
        "effects": effects,
    }


def _aggregate_matches_result(
    aggregate: AggregateConcern,
    result: ConcernPolicyResult,
) -> bool:
    if result.target and aggregate.anchor == result.object_drug:
        return result.target in aggregate.targets

    if result.effect_id and aggregate.effect_id:
        return result.effect_id in aggregate.effect_id.split(", ")

    return False


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


def _unique_sorted(values) -> tuple[str, ...]:
    return tuple(sorted({value for value in values if value}))
