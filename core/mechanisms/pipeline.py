"""
This module centralizes the read-only mechanism pipeline:

Facts
-> MechanismEffect
-> InteractionCandidate
-> ArbitrationResult
-> ConcernPolicyResult
-> AggregateConcern

It does not change existing rule evaluation or clinical output.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.mechanisms.aggregation import (
    AggregateConcern,
    aggregate_policy_results,
)
from core.mechanisms.arbitration import (
    ArbitrationResult,
    arbitrate_candidates,
)
from core.mechanisms.candidates import (
    InteractionCandidate,
    find_interaction_candidates,
)
from core.mechanisms.effects import MechanismEffect
from core.mechanisms.inference import infer_mechanism_effects_for_drugs
from core.mechanisms.policy import (
    ConcernPolicyResult,
    apply_concern_policy,
)
from core.mechanisms.scoring import ScoredConcern, score_policy_results
from core.mechanisms.severity import (
    SeverityAnnotatedConcern,
    annotate_preliminary_severity,
)
from core.models import Facts


@dataclass(frozen=True)
class MechanismPipelineResult:
    """Container for each stage of the normalized mechanism pipeline."""

    effects: tuple[MechanismEffect, ...]
    candidates: tuple[InteractionCandidate, ...]
    arbitration_results: tuple[ArbitrationResult, ...]
    policy_results: tuple[ConcernPolicyResult, ...]
    scored_concerns: tuple[ScoredConcern, ...]
    severity_annotations: tuple[SeverityAnnotatedConcern, ...]
    aggregate_concerns: tuple[AggregateConcern, ...]

def run_mechanism_pipeline(
    drug_ids: list[str],
    facts: Facts,
) -> MechanismPipelineResult:
    """Run the read-only normalized mechanism pipeline for selected drugs."""
    effects = infer_mechanism_effects_for_drugs(drug_ids, facts)
    candidates = find_interaction_candidates(effects)
    arbitration_results = arbitrate_candidates(candidates)
    policy_results = apply_concern_policy(arbitration_results)
    aggregate_concerns = aggregate_policy_results(policy_results)
    scored_concerns = score_policy_results(policy_results, aggregate_concerns)
    severity_annotations = annotate_preliminary_severity(scored_concerns)

    return MechanismPipelineResult(
        effects=tuple(effects),
        candidates=tuple(candidates),
        arbitration_results=tuple(arbitration_results),
        policy_results=tuple(policy_results),
        scored_concerns=tuple(scored_concerns),
        severity_annotations=tuple(severity_annotations),
        aggregate_concerns=tuple(aggregate_concerns),
    )