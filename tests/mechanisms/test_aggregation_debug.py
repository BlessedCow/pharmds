from core.mechanisms.aggregation import (
    AGGREGATE_OBJECT_EXPOSURE_INCREASE,
    AGGREGATE_SHARED_PD_EFFECT,
    AggregateConcern,
)
from core.mechanisms.aggregation_debug import (
    format_aggregate_concern,
    format_aggregate_concerns,
)
from core.mechanisms.arbitration import CONCERN_ADDITIVE_PD_EFFECT
from core.mechanisms.candidates import CANDIDATE_PD_SHARED_EFFECT
from core.mechanisms.policy import (
    POLICY_MECHANISTIC_CONCERN,
    POLICY_TOLERABILITY_CONCERN,
    ConcernPolicyResult,
)


def test_format_aggregate_concern_with_targets():
    concern = AggregateConcern(
        aggregate_type=AGGREGATE_OBJECT_EXPOSURE_INCREASE,
        anchor="vortioxetine",
        policy_concern=POLICY_MECHANISTIC_CONCERN,
        drugs=("bupropion", "fluconazole", "vortioxetine"),
        targets=("CYP2D6", "CYP3A4"),
        members=(
            ConcernPolicyResult(
                policy_concern=POLICY_MECHANISTIC_CONCERN,
                source_concern="exposure_increase",
                precipitant_drug="bupropion",
                object_drug="vortioxetine",
                target="CYP2D6",
            ),
        ),
    )

    assert format_aggregate_concern(concern) == (
        "object_exposure_increase_cluster: vortioxetine "
        "| policy_concern=mechanistic_concern "
        "| drugs=bupropion, fluconazole, vortioxetine "
        "| targets=CYP2D6, CYP3A4 "
        "| members=1"
    )


def test_format_aggregate_concern_with_effect_id():
    concern = AggregateConcern(
        aggregate_type=AGGREGATE_SHARED_PD_EFFECT,
        anchor="nausea",
        policy_concern=POLICY_TOLERABILITY_CONCERN,
        drugs=("fluconazole", "vortioxetine"),
        effect_id="nausea",
        members=(
            ConcernPolicyResult(
                policy_concern=POLICY_TOLERABILITY_CONCERN,
                source_concern=CONCERN_ADDITIVE_PD_EFFECT,
                precipitant_drug="fluconazole",
                object_drug="vortioxetine",
                effect_id="nausea",
                candidate_type=CANDIDATE_PD_SHARED_EFFECT,
            ),
        ),
    )

    assert format_aggregate_concern(concern) == (
        "shared_pd_effect_cluster: nausea "
        "| policy_concern=tolerability_concern "
        "| drugs=fluconazole, vortioxetine "
        "| effect=nausea "
        "| members=1"
    )


def test_format_aggregate_concerns_formats_multiple():
    concerns = [
        AggregateConcern(
            aggregate_type=AGGREGATE_OBJECT_EXPOSURE_INCREASE,
            anchor="vortioxetine",
            policy_concern=POLICY_MECHANISTIC_CONCERN,
            drugs=("bupropion", "vortioxetine"),
            targets=("CYP2D6",),
        ),
        AggregateConcern(
            aggregate_type=AGGREGATE_SHARED_PD_EFFECT,
            anchor="nausea",
            policy_concern=POLICY_TOLERABILITY_CONCERN,
            drugs=("fluconazole", "vortioxetine"),
            effect_id="nausea",
        ),
    ]

    assert format_aggregate_concerns(concerns) == [
        (
            "object_exposure_increase_cluster: vortioxetine "
            "| policy_concern=mechanistic_concern "
            "| drugs=bupropion, vortioxetine "
            "| targets=CYP2D6 "
            "| members=0"
        ),
        (
            "shared_pd_effect_cluster: nausea "
            "| policy_concern=tolerability_concern "
            "| drugs=fluconazole, vortioxetine "
            "| effect=nausea "
            "| members=0"
        ),
    ]
