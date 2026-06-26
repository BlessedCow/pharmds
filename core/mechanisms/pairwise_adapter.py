"""Internal adapter for comparing mechanism output to pairwise-style output.

This module is intentionally not wired into CLI, Streamlit, or public JSON
payloads. It only shapes mechanism pipeline results for migration comparison.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.mechanisms.aggregation import AggregateConcern
from core.mechanisms.pipeline import MechanismPipelineResult
from core.mechanisms.policy import (
    POLICY_EXPOSURE_REDUCTION_CONCERN,
    POLICY_MECHANISTIC_CONCERN,
    POLICY_SAFETY_CONCERN,
    POLICY_TOLERABILITY_CONCERN,
    ConcernPolicyResult,
)
from core.mechanisms.severity import PRELIMINARY_SEVERITY_UNSCORED

PAIRWISE_ADAPTER_DOMAIN_PK = "PK"
PAIRWISE_ADAPTER_DOMAIN_PD = "PD"
PAIRWISE_ADAPTER_DOMAIN_UNKNOWN = "unknown"


@dataclass(frozen=True)
class PairwiseMechanismConcern:
    """Pairwise-shaped concern derived from mechanism pipeline output."""

    pair_key: tuple[str, str]
    precipitant_drug: str
    object_drug: str
    domain: str
    concern_id: str
    policy_concern: str
    source_concern: str
    severity: str = PRELIMINARY_SEVERITY_UNSCORED
    confidence: str = "unscored"
    target: str | None = None
    effect_id: str | None = None
    candidate_type: str | None = None
    explanation: str = ""
    explanation_fields: dict[str, Any] = field(default_factory=dict)


def adapt_mechanism_pipeline_to_pairwise(
    pipeline: MechanismPipelineResult,
) -> tuple[PairwiseMechanismConcern, ...]:
    """Shape mechanism policy results into pairwise-style comparison objects."""
    severity_by_key = {
        annotation.key: annotation
        for annotation in pipeline.severity_annotations
    }

    return tuple(
        _policy_result_to_pairwise_concern(
            policy,
            severity=(
                severity_by_key.get(policy.key).preliminary_severity
                if policy.key in severity_by_key
                else policy.severity
            ),
            aggregates=pipeline.aggregate_concerns,
        )
        for policy in pipeline.policy_results
    )


def _policy_result_to_pairwise_concern(
    policy: ConcernPolicyResult,
    *,
    severity: str,
    aggregates: tuple[AggregateConcern, ...],
) -> PairwiseMechanismConcern:
    aggregate_context = _aggregate_context_for_policy(policy, aggregates)

    return PairwiseMechanismConcern(
        pair_key=_pair_key(policy.precipitant_drug, policy.object_drug),
        precipitant_drug=policy.precipitant_drug,
        object_drug=policy.object_drug,
        domain=_domain_for_policy_concern(policy.policy_concern),
        concern_id=_concern_id_for_policy(policy),
        policy_concern=policy.policy_concern,
        source_concern=policy.source_concern,
        severity=severity,
        confidence=policy.confidence,
        target=policy.target,
        effect_id=policy.effect_id,
        candidate_type=policy.candidate_type,
        explanation=policy.explanation,
        explanation_fields={
            "precipitant_drug": policy.precipitant_drug,
            "object_drug": policy.object_drug,
            "target": policy.target,
            "effect_id": policy.effect_id,
            "candidate_type": policy.candidate_type,
            "aggregate_types": aggregate_context["aggregate_types"],
            "aggregate_targets": aggregate_context["aggregate_targets"],
            "aggregate_effects": aggregate_context["aggregate_effects"],
        },
    )


def _pair_key(first_drug: str, second_drug: str) -> tuple[str, str]:
    return tuple(sorted((first_drug, second_drug)))


def _domain_for_policy_concern(policy_concern: str) -> str:
    if policy_concern in {
        POLICY_MECHANISTIC_CONCERN,
        POLICY_EXPOSURE_REDUCTION_CONCERN,
    }:
        return PAIRWISE_ADAPTER_DOMAIN_PK

    if policy_concern in {
        POLICY_SAFETY_CONCERN,
        POLICY_TOLERABILITY_CONCERN,
    }:
        return PAIRWISE_ADAPTER_DOMAIN_PD

    return PAIRWISE_ADAPTER_DOMAIN_UNKNOWN


def _concern_id_for_policy(policy: ConcernPolicyResult) -> str:
    if policy.target:
        return policy.target

    if policy.effect_id:
        return policy.effect_id

    return policy.source_concern


def _aggregate_context_for_policy(
    policy: ConcernPolicyResult,
    aggregates: tuple[AggregateConcern, ...],
) -> dict[str, tuple[str, ...]]:
    matching = [
        aggregate
        for aggregate in aggregates
        if policy in aggregate.members
    ]

    return {
        "aggregate_types": _unique_sorted(
            aggregate.aggregate_type
            for aggregate in matching
        ),
        "aggregate_targets": _unique_sorted(
            target
            for aggregate in matching
            for target in aggregate.targets
        ),
        "aggregate_effects": _unique_sorted(
            aggregate.effect_id
            for aggregate in matching
            if aggregate.effect_id
        ),
    }


def _unique_sorted(values) -> tuple[str, ...]:
    return tuple(sorted({value for value in values if value}))