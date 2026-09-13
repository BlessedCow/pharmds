from __future__ import annotations

from core.mechanisms.aggregate_summary import AggregateConcernSummary
from core.mechanisms.aggregation import (
    AGGREGATE_SAFETY_CONCERN,
    AGGREGATE_SHARED_PD_EFFECT,
    AGGREGATE_TOLERABILITY_CONCERN,
    AggregateConcern,
)
from core.mechanisms.policy import ConcernPolicyResult
from core.mechanisms.result_summary import (
    _consolidate_public_aggregate_summaries,
)


def _policy_member(
    *,
    concern: str,
    effect_id: str,
    a: str,
    b: str,
) -> ConcernPolicyResult:
    return ConcernPolicyResult(
        source_concern=concern,
        policy_concern=concern,
        precipitant_drug=a,
        object_drug=b,
        target=None,
        effect_id=effect_id,
        explanation="test",
    )


def _summary(aggregate: AggregateConcern) -> AggregateConcernSummary:
    return AggregateConcernSummary(
        aggregate=aggregate,
        severity_annotation=None,
        evidence_summary=None,
        patient_risk_modifiers=(),
        risk_context=None,
        evidence_conflict_level="none",
        evidence_conflict_message=None,
        narrative=None,
    )


def test_redundant_single_effect_safety_summary_is_suppressed() -> None:
    drugs = ("alprazolam", "clonazepam", "lorazepam")
    member = _policy_member(
        concern="safety_concern",
        effect_id="respiratory_depression",
        a="alprazolam",
        b="clonazepam",
    )

    shared = _summary(
        AggregateConcern(
            aggregate_type=AGGREGATE_SHARED_PD_EFFECT,
            anchor="respiratory_depression",
            policy_concern="safety_concern",
            drugs=drugs,
            effect_id="respiratory_depression",
            members=(member,),
        )
    )
    broad = _summary(
        AggregateConcern(
            aggregate_type=AGGREGATE_SAFETY_CONCERN,
            anchor="safety_concern",
            policy_concern="safety_concern",
            drugs=drugs,
            effect_id="respiratory_depression",
            members=(member,),
        )
    )

    assert _consolidate_public_aggregate_summaries([shared, broad]) == [shared]


def test_redundant_multi_effect_tolerability_summary_is_suppressed() -> None:
    drugs = ("alprazolam", "clonazepam", "lorazepam")
    cns = _policy_member(
        concern="tolerability_concern",
        effect_id="CNS_depression",
        a="alprazolam",
        b="clonazepam",
    )
    sedation = _policy_member(
        concern="tolerability_concern",
        effect_id="sedation",
        a="alprazolam",
        b="clonazepam",
    )

    shared_cns = _summary(
        AggregateConcern(
            aggregate_type=AGGREGATE_SHARED_PD_EFFECT,
            anchor="CNS_depression",
            policy_concern="tolerability_concern",
            drugs=drugs,
            effect_id="CNS_depression",
            members=(cns,),
        )
    )
    shared_sedation = _summary(
        AggregateConcern(
            aggregate_type=AGGREGATE_SHARED_PD_EFFECT,
            anchor="sedation",
            policy_concern="tolerability_concern",
            drugs=drugs,
            effect_id="sedation",
            members=(sedation,),
        )
    )
    broad = _summary(
        AggregateConcern(
            aggregate_type=AGGREGATE_TOLERABILITY_CONCERN,
            anchor="tolerability_concern",
            policy_concern="tolerability_concern",
            drugs=drugs,
            effect_id="CNS_depression, sedation",
            members=(cns, sedation),
        )
    )

    assert _consolidate_public_aggregate_summaries(
        [shared_cns, shared_sedation, broad]
    ) == [shared_cns, shared_sedation]


def test_broad_summary_is_kept_when_not_all_effects_are_represented() -> None:
    drugs = ("drug_a", "drug_b", "drug_c")
    cns = _policy_member(
        concern="tolerability_concern",
        effect_id="CNS_depression",
        a="drug_a",
        b="drug_b",
    )
    sedation = _policy_member(
        concern="tolerability_concern",
        effect_id="sedation",
        a="drug_b",
        b="drug_c",
    )

    shared_cns = _summary(
        AggregateConcern(
            aggregate_type=AGGREGATE_SHARED_PD_EFFECT,
            anchor="CNS_depression",
            policy_concern="tolerability_concern",
            drugs=drugs,
            effect_id="CNS_depression",
            members=(cns,),
        )
    )
    broad = _summary(
        AggregateConcern(
            aggregate_type=AGGREGATE_TOLERABILITY_CONCERN,
            anchor="tolerability_concern",
            policy_concern="tolerability_concern",
            drugs=drugs,
            effect_id="CNS_depression, sedation",
            members=(cns, sedation),
        )
    )

    assert _consolidate_public_aggregate_summaries(
        [shared_cns, broad]
    ) == [shared_cns, broad]


def test_broad_summary_is_kept_when_drug_sets_differ() -> None:
    cns = _policy_member(
        concern="tolerability_concern",
        effect_id="CNS_depression",
        a="drug_a",
        b="drug_b",
    )

    shared = _summary(
        AggregateConcern(
            aggregate_type=AGGREGATE_SHARED_PD_EFFECT,
            anchor="CNS_depression",
            policy_concern="tolerability_concern",
            drugs=("drug_a", "drug_b"),
            effect_id="CNS_depression",
            members=(cns,),
        )
    )
    broad = _summary(
        AggregateConcern(
            aggregate_type=AGGREGATE_TOLERABILITY_CONCERN,
            anchor="tolerability_concern",
            policy_concern="tolerability_concern",
            drugs=("drug_a", "drug_b", "drug_c"),
            effect_id="CNS_depression",
            members=(cns,),
        )
    )

    assert _consolidate_public_aggregate_summaries(
        [shared, broad]
    ) == [shared, broad]
