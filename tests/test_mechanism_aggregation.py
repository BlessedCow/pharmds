from core.mechanism_aggregation import (
    AGGREGATE_OBJECT_EXPOSURE_DECREASE,
    AGGREGATE_OBJECT_EXPOSURE_INCREASE,
    AGGREGATE_SAFETY_CONCERN,
    AGGREGATE_SHARED_PD_EFFECT,
    AGGREGATE_TOLERABILITY_CONCERN,
    AggregateConcern,
    aggregate_policy_results,
    dedupe_aggregate_concerns,
)
from core.mechanism_arbitration import (
    CONCERN_ADDITIVE_PD_EFFECT,
    CONCERN_EXPOSURE_DECREASE,
    CONCERN_EXPOSURE_INCREASE,
)
from core.mechanism_candidates import (
    CANDIDATE_ENZYME_INDUCTION,
    CANDIDATE_ENZYME_INHIBITION,
    CANDIDATE_PD_SHARED_EFFECT,
)
from core.mechanism_policy import (
    POLICY_EXPOSURE_REDUCTION_CONCERN,
    POLICY_MECHANISTIC_CONCERN,
    POLICY_SAFETY_CONCERN,
    POLICY_TOLERABILITY_CONCERN,
    ConcernPolicyResult,
)


def test_aggregates_object_exposure_increase_by_object_drug():
    results = [
        ConcernPolicyResult(
            policy_concern=POLICY_MECHANISTIC_CONCERN,
            source_concern=CONCERN_EXPOSURE_INCREASE,
            precipitant_drug="bupropion",
            object_drug="vortioxetine",
            target="CYP2D6",
            candidate_type=CANDIDATE_ENZYME_INHIBITION,
        ),
        ConcernPolicyResult(
            policy_concern=POLICY_MECHANISTIC_CONCERN,
            source_concern=CONCERN_EXPOSURE_INCREASE,
            precipitant_drug="fluconazole",
            object_drug="vortioxetine",
            target="CYP3A4",
            candidate_type=CANDIDATE_ENZYME_INHIBITION,
        ),
    ]

    aggregates = aggregate_policy_results(results)

    exposure_clusters = [
        item
        for item in aggregates
        if item.aggregate_type == AGGREGATE_OBJECT_EXPOSURE_INCREASE
    ]

    assert len(exposure_clusters) == 1
    assert exposure_clusters[0].anchor == "vortioxetine"
    assert exposure_clusters[0].drugs == (
        "bupropion",
        "fluconazole",
        "vortioxetine",
    )
    assert exposure_clusters[0].targets == ("CYP2D6", "CYP3A4")
    assert len(exposure_clusters[0].members) == 2


def test_aggregates_object_exposure_decrease_by_object_drug():
    results = [
        ConcernPolicyResult(
            policy_concern=POLICY_EXPOSURE_REDUCTION_CONCERN,
            source_concern=CONCERN_EXPOSURE_DECREASE,
            precipitant_drug="rifampin",
            object_drug="vortioxetine",
            target="CYP3A4",
            candidate_type=CANDIDATE_ENZYME_INDUCTION,
        )
    ]

    aggregates = aggregate_policy_results(results)

    exposure_clusters = [
        item
        for item in aggregates
        if item.aggregate_type == AGGREGATE_OBJECT_EXPOSURE_DECREASE
    ]

    assert len(exposure_clusters) == 1
    assert exposure_clusters[0].anchor == "vortioxetine"
    assert exposure_clusters[0].targets == ("CYP3A4",)
    assert exposure_clusters[0].drugs == ("rifampin", "vortioxetine")


def test_aggregates_shared_pd_effect_by_effect_id():
    results = [
        ConcernPolicyResult(
            policy_concern=POLICY_TOLERABILITY_CONCERN,
            source_concern=CONCERN_ADDITIVE_PD_EFFECT,
            precipitant_drug="fluconazole",
            object_drug="vortioxetine",
            effect_id="nausea",
            candidate_type=CANDIDATE_PD_SHARED_EFFECT,
        ),
        ConcernPolicyResult(
            policy_concern=POLICY_TOLERABILITY_CONCERN,
            source_concern=CONCERN_ADDITIVE_PD_EFFECT,
            precipitant_drug="clarithromycin",
            object_drug="vortioxetine",
            effect_id="nausea",
            candidate_type=CANDIDATE_PD_SHARED_EFFECT,
        ),
    ]

    aggregates = aggregate_policy_results(results)

    pd_clusters = [
        item
        for item in aggregates
        if item.aggregate_type == AGGREGATE_SHARED_PD_EFFECT
    ]

    assert len(pd_clusters) == 1
    assert pd_clusters[0].anchor == "nausea"
    assert pd_clusters[0].effect_id == "nausea"
    assert pd_clusters[0].drugs == (
        "clarithromycin",
        "fluconazole",
        "vortioxetine",
    )
    assert len(pd_clusters[0].members) == 2


def test_aggregates_safety_concerns():
    results = [
        ConcernPolicyResult(
            policy_concern=POLICY_SAFETY_CONCERN,
            source_concern=CONCERN_ADDITIVE_PD_EFFECT,
            precipitant_drug="clarithromycin",
            object_drug="fluconazole",
            effect_id="QT_prolongation",
            candidate_type=CANDIDATE_PD_SHARED_EFFECT,
        )
    ]

    aggregates = aggregate_policy_results(results)

    safety_clusters = [
        item
        for item in aggregates
        if item.aggregate_type == AGGREGATE_SAFETY_CONCERN
    ]

    assert len(safety_clusters) == 1
    assert safety_clusters[0].anchor == POLICY_SAFETY_CONCERN
    assert safety_clusters[0].effect_id == "QT_prolongation"
    assert safety_clusters[0].drugs == ("clarithromycin", "fluconazole")


def test_aggregates_tolerability_concerns():
    results = [
        ConcernPolicyResult(
            policy_concern=POLICY_TOLERABILITY_CONCERN,
            source_concern=CONCERN_ADDITIVE_PD_EFFECT,
            precipitant_drug="fluconazole",
            object_drug="vortioxetine",
            effect_id="nausea",
            candidate_type=CANDIDATE_PD_SHARED_EFFECT,
        )
    ]

    aggregates = aggregate_policy_results(results)

    tolerability_clusters = [
        item
        for item in aggregates
        if item.aggregate_type == AGGREGATE_TOLERABILITY_CONCERN
    ]

    assert len(tolerability_clusters) == 1
    assert tolerability_clusters[0].anchor == POLICY_TOLERABILITY_CONCERN
    assert tolerability_clusters[0].effect_id == "nausea"
    assert tolerability_clusters[0].drugs == ("fluconazole", "vortioxetine")


def test_dedupe_aggregate_concerns_preserves_first_seen_order():
    concerns = [
        AggregateConcern(
            aggregate_type=AGGREGATE_SHARED_PD_EFFECT,
            anchor="nausea",
            policy_concern=POLICY_TOLERABILITY_CONCERN,
            drugs=("fluconazole", "vortioxetine"),
            effect_id="nausea",
        ),
        AggregateConcern(
            aggregate_type=AGGREGATE_SHARED_PD_EFFECT,
            anchor="nausea",
            policy_concern=POLICY_TOLERABILITY_CONCERN,
            drugs=("fluconazole", "vortioxetine"),
            effect_id="nausea",
        ),
        AggregateConcern(
            aggregate_type=AGGREGATE_SHARED_PD_EFFECT,
            anchor="QT_prolongation",
            policy_concern=POLICY_SAFETY_CONCERN,
            drugs=("clarithromycin", "fluconazole"),
            effect_id="QT_prolongation",
        ),
    ]

    deduped = dedupe_aggregate_concerns(concerns)

    assert len(deduped) == 2
    assert deduped[0].anchor == "nausea"
    assert deduped[1].anchor == "QT_prolongation"