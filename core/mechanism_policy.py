from __future__ import annotations

from dataclasses import dataclass

from core.mechanism_arbitration import (
    CONCERN_ADDITIVE_PD_EFFECT,
    CONCERN_EXPOSURE_DECREASE,
    CONCERN_EXPOSURE_INCREASE,
    ArbitrationResult,
)

POLICY_MECHANISTIC_CONCERN = "mechanistic_concern"
POLICY_EXPOSURE_REDUCTION_CONCERN = "exposure_reduction_concern"
POLICY_TOLERABILITY_CONCERN = "tolerability_concern"
POLICY_SAFETY_CONCERN = "safety_concern"
POLICY_UNKNOWN_CONCERN = "unknown_concern"

# Conservative first-pass mapping. This is intentionally small.
SAFETY_PD_EFFECTS = {
    "QT_prolongation",
    "respiratory_depression",
    "seizure_risk",
    "seizure_threshold",
    "serotonin_syndrome",
    "bleeding",
    "bradycardia",
}

TOLERABILITY_PD_EFFECTS = {
    "nausea",
    "insomnia_risk",
    "activation_agitation_risk",
    "sedation",
    "CNS_depression",
}


@dataclass(frozen=True)
class ConcernPolicyResult:
    """Policy-level classification of an arbitration result.

    This is still not final clinical severity.

    Attributes:
        policy_concern: Broad policy concern bucket.
        source_concern: Concern label from ArbitrationResult.
        precipitant_drug: Drug causing the mechanism/effect.
        object_drug: Drug affected by the mechanism/effect.
        target: Enzyme/transporter target when applicable.
        effect_id: PD effect id when applicable.
        candidate_type: Source candidate type.
        confidence: Carried through from ArbitrationResult.
        severity: Carried through from ArbitrationResult.
        explanation: Human-readable explanation from ArbitrationResult.
    """

    policy_concern: str
    source_concern: str
    precipitant_drug: str
    object_drug: str
    target: str | None = None
    effect_id: str | None = None
    candidate_type: str | None = None
    confidence: str = "unscored"
    severity: str = "unscored"
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


def apply_concern_policy(
    results: list[ArbitrationResult],
) -> list[ConcernPolicyResult]:
    """Classify arbitration results into policy concern buckets."""
    policy_results = [
        arbitration_result_to_policy_result(result)
        for result in results
    ]

    return dedupe_policy_results(policy_results)


def arbitration_result_to_policy_result(
    result: ArbitrationResult,
) -> ConcernPolicyResult:
    """Convert one ArbitrationResult into a ConcernPolicyResult."""
    return ConcernPolicyResult(
        policy_concern=_policy_concern_for_result(result),
        source_concern=result.concern,
        precipitant_drug=result.precipitant_drug,
        object_drug=result.object_drug,
        target=result.target,
        effect_id=result.effect_id,
        candidate_type=result.candidate_type,
        confidence=result.confidence,
        severity=result.severity,
        explanation=result.explanation,
    )


def _policy_concern_for_result(result: ArbitrationResult) -> str:
    if result.concern == CONCERN_EXPOSURE_INCREASE:
        return POLICY_MECHANISTIC_CONCERN

    if result.concern == CONCERN_EXPOSURE_DECREASE:
        return POLICY_EXPOSURE_REDUCTION_CONCERN

    if result.concern == CONCERN_ADDITIVE_PD_EFFECT:
        return _policy_concern_for_pd_effect(result.effect_id)

    return POLICY_UNKNOWN_CONCERN


def _policy_concern_for_pd_effect(effect_id: str | None) -> str:
    if effect_id in SAFETY_PD_EFFECTS:
        return POLICY_SAFETY_CONCERN

    if effect_id in TOLERABILITY_PD_EFFECTS:
        return POLICY_TOLERABILITY_CONCERN

    return POLICY_UNKNOWN_CONCERN


def dedupe_policy_results(
    results: list[ConcernPolicyResult],
) -> list[ConcernPolicyResult]:
    """Deduplicate policy results while preserving first-seen order."""
    seen: set[tuple[str, str, str, str | None, str | None]] = set()
    out: list[ConcernPolicyResult] = []

    for result in results:
        if result.key in seen:
            continue
        seen.add(result.key)
        out.append(result)

    return out