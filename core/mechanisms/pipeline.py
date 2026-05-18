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

from core.evidence.gating import (
    EVIDENCE_MODE_OFF,
    EVIDENCE_MODE_SUPPORTED,
    filter_facts_to_evidence_backed_pd_effects,
    require_valid_evidence_mode,
)
from core.mechanisms.aggregate_evidence import (
    AggregateEvidenceSummary,
    summarize_aggregate_evidence,
)
from core.mechanisms.aggregate_severity import (
    AggregateSeverityAnnotation,
    annotate_aggregate_preliminary_severity,
)
from core.mechanisms.aggregate_summary import (
    AggregateConcernSummary,
    build_aggregate_concern_summaries,
)
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
    """Container for all read-only mechanism pipeline stages."""

    effects: tuple[MechanismEffect, ...]
    candidates: tuple[InteractionCandidate, ...]
    arbitration_results: tuple[ArbitrationResult, ...]
    policy_results: tuple[ConcernPolicyResult, ...]
    scored_concerns: tuple[ScoredConcern, ...]
    severity_annotations: tuple[SeverityAnnotatedConcern, ...]
    aggregate_concerns: tuple[AggregateConcern, ...]
    aggregate_severity_annotations: tuple[
        AggregateSeverityAnnotation,
        ...,
    ]
    aggregate_evidence_summaries: tuple[
        AggregateEvidenceSummary,
        ...,
    ]
    aggregate_concern_summaries: tuple[
        AggregateConcernSummary,
        ...,
    ]
def run_mechanism_pipeline(
    drug_ids: list[str],
    facts: Facts,
    *,
    evidence_gated: bool = False,
    evidence_mode: str = EVIDENCE_MODE_OFF,
) -> MechanismPipelineResult:
    """Run the read-only normalized mechanism pipeline for selected drugs."""
    if evidence_gated and evidence_mode == EVIDENCE_MODE_OFF:
        evidence_mode = EVIDENCE_MODE_SUPPORTED

    require_valid_evidence_mode(evidence_mode)

    pipeline_facts = facts

    if evidence_mode != EVIDENCE_MODE_OFF:
        pipeline_facts = filter_facts_to_evidence_backed_pd_effects(
            facts,
            mode=evidence_mode,
        )

    effects = infer_mechanism_effects_for_drugs(drug_ids, pipeline_facts)
    candidates = find_interaction_candidates(effects)
    arbitration_results = arbitrate_candidates(candidates)
    policy_results = apply_concern_policy(arbitration_results)
    aggregate_concerns = aggregate_policy_results(policy_results)
    scored_concerns = score_policy_results(policy_results, aggregate_concerns)
    severity_annotations = annotate_preliminary_severity(scored_concerns)
    aggregate_severity_annotations = annotate_aggregate_preliminary_severity(
        aggregate_concerns,
        severity_annotations,
    )
    aggregate_evidence_summaries = summarize_aggregate_evidence(
    aggregate_concerns,
    )
    aggregate_concern_summaries = build_aggregate_concern_summaries(
        aggregate_concerns,
        aggregate_severity_annotations,
        aggregate_evidence_summaries,
    )

    return MechanismPipelineResult(
        effects=tuple(effects),
        candidates=tuple(candidates),
        arbitration_results=tuple(arbitration_results),
        policy_results=tuple(policy_results),
        scored_concerns=tuple(scored_concerns),
        severity_annotations=tuple(severity_annotations),
        aggregate_concerns=tuple(aggregate_concerns),
        aggregate_severity_annotations=tuple(
            aggregate_severity_annotations,
        ),
        aggregate_evidence_summaries=tuple(
            aggregate_evidence_summaries
        ),
                aggregate_concern_summaries=tuple(
            aggregate_concern_summaries,
        ),
    )