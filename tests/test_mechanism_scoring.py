from core.mechanism_aggregation import (
    AGGREGATE_OBJECT_EXPOSURE_INCREASE,
    AGGREGATE_SHARED_PD_EFFECT,
    AggregateConcern,
)
from core.mechanism_arbitration import (
    CONCERN_ADDITIVE_PD_EFFECT,
    CONCERN_EXPOSURE_INCREASE,
)
from core.mechanism_candidates import (
    CANDIDATE_ENZYME_INHIBITION,
    CANDIDATE_PD_SHARED_EFFECT,
)
from core.mechanism_policy import (
    POLICY_MECHANISTIC_CONCERN,
    POLICY_SAFETY_CONCERN,
    POLICY_TOLERABILITY_CONCERN,
    POLICY_UNKNOWN_CONCERN,
    ConcernPolicyResult,
)
from core.mechanism_scoring import (
    CONFIDENCE_HIGH,
    CONFIDENCE_LOW,
    CONFIDENCE_MODERATE,
    SEVERITY_UNSCORED,
    ScoredConcern,
    dedupe_scored_concerns,
    policy_result_to_scored_concern,
    score_policy_results,
)


def test_scores_mechanistic_enzyme_candidate_as_high_confidence():
    result = ConcernPolicyResult(
        policy_concern=POLICY_MECHANISTIC_CONCERN,
        source_concern=CONCERN_EXPOSURE_INCREASE,
        precipitant_drug="bupropion",
        object_drug="vortioxetine",
        target="CYP2D6",
        candidate_type=CANDIDATE_ENZYME_INHIBITION,
    )

    scored = policy_result_to_scored_concern(result)

    assert scored.confidence == CONFIDENCE_HIGH
    assert scored.severity == SEVERITY_UNSCORED
    assert scored.precipitant_drug == "bupropion"
    assert scored.object_drug == "vortioxetine"
    assert scored.target == "CYP2D6"


def test_scores_shared_safety_pd_effect_as_high_confidence():
    result = ConcernPolicyResult(
        policy_concern=POLICY_SAFETY_CONCERN,
        source_concern=CONCERN_ADDITIVE_PD_EFFECT,
        precipitant_drug="clarithromycin",
        object_drug="fluconazole",
        effect_id="QT_prolongation",
        candidate_type=CANDIDATE_PD_SHARED_EFFECT,
    )

    scored = policy_result_to_scored_concern(result)

    assert scored.confidence == CONFIDENCE_HIGH
    assert scored.severity == SEVERITY_UNSCORED
    assert scored.effect_id == "QT_prolongation"


def test_scores_shared_tolerability_pd_effect_as_moderate_confidence():
    result = ConcernPolicyResult(
        policy_concern=POLICY_TOLERABILITY_CONCERN,
        source_concern=CONCERN_ADDITIVE_PD_EFFECT,
        precipitant_drug="fluconazole",
        object_drug="vortioxetine",
        effect_id="nausea",
        candidate_type=CANDIDATE_PD_SHARED_EFFECT,
    )

    scored = policy_result_to_scored_concern(result)

    assert scored.confidence == CONFIDENCE_MODERATE
    assert scored.severity == SEVERITY_UNSCORED
    assert scored.effect_id == "nausea"


def test_scores_unknown_policy_concern_as_low_confidence():
    result = ConcernPolicyResult(
        policy_concern=POLICY_UNKNOWN_CONCERN,
        source_concern="unknown",
        precipitant_drug="drug_a",
        object_drug="drug_b",
        effect_id="uncategorized_effect",
        candidate_type="UNKNOWN_CANDIDATE",
    )

    scored = policy_result_to_scored_concern(result)

    assert scored.confidence == CONFIDENCE_LOW
    assert scored.severity == SEVERITY_UNSCORED


def test_score_policy_results_maps_multiple_results():
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
            policy_concern=POLICY_TOLERABILITY_CONCERN,
            source_concern=CONCERN_ADDITIVE_PD_EFFECT,
            precipitant_drug="fluconazole",
            object_drug="vortioxetine",
            effect_id="nausea",
            candidate_type=CANDIDATE_PD_SHARED_EFFECT,
        ),
    ]

    scored = score_policy_results(results)

    assert len(scored) == 2
    assert scored[0].confidence == CONFIDENCE_HIGH
    assert scored[1].confidence == CONFIDENCE_MODERATE


def test_dedupe_scored_concerns_preserves_first_seen_order():
    concerns = [
        ScoredConcern(
            policy_concern=POLICY_TOLERABILITY_CONCERN,
            source_concern=CONCERN_ADDITIVE_PD_EFFECT,
            precipitant_drug="fluconazole",
            object_drug="vortioxetine",
            effect_id="nausea",
            candidate_type=CANDIDATE_PD_SHARED_EFFECT,
            confidence=CONFIDENCE_MODERATE,
        ),
        ScoredConcern(
            policy_concern=POLICY_TOLERABILITY_CONCERN,
            source_concern=CONCERN_ADDITIVE_PD_EFFECT,
            precipitant_drug="fluconazole",
            object_drug="vortioxetine",
            effect_id="nausea",
            candidate_type=CANDIDATE_PD_SHARED_EFFECT,
            confidence=CONFIDENCE_MODERATE,
        ),
        ScoredConcern(
            policy_concern=POLICY_SAFETY_CONCERN,
            source_concern=CONCERN_ADDITIVE_PD_EFFECT,
            precipitant_drug="clarithromycin",
            object_drug="fluconazole",
            effect_id="QT_prolongation",
            candidate_type=CANDIDATE_PD_SHARED_EFFECT,
            confidence=CONFIDENCE_HIGH,
        ),
    ]

    deduped = dedupe_scored_concerns(concerns)

    assert len(deduped) == 2
    assert deduped[0].effect_id == "nausea"
    assert deduped[1].effect_id == "QT_prolongation"
def test_scored_concern_carries_object_exposure_aggregate_context():
    result = ConcernPolicyResult(
        policy_concern=POLICY_MECHANISTIC_CONCERN,
        source_concern=CONCERN_EXPOSURE_INCREASE,
        precipitant_drug="bupropion",
        object_drug="vortioxetine",
        target="CYP2D6",
        candidate_type=CANDIDATE_ENZYME_INHIBITION,
    )
    aggregates = [
        AggregateConcern(
            aggregate_type=AGGREGATE_OBJECT_EXPOSURE_INCREASE,
            anchor="vortioxetine",
            policy_concern=POLICY_MECHANISTIC_CONCERN,
            drugs=("bupropion", "fluconazole", "vortioxetine"),
            targets=("CYP2C19", "CYP2D6"),
            members=(result,),
        )
    ]

    scored = policy_result_to_scored_concern(result, aggregates)

    assert scored.aggregate_member_count == 1
    assert scored.related_targets == ("CYP2C19", "CYP2D6")
    assert scored.related_effects == ()


def test_scored_concern_carries_shared_pd_effect_aggregate_context():
    result = ConcernPolicyResult(
        policy_concern=POLICY_TOLERABILITY_CONCERN,
        source_concern=CONCERN_ADDITIVE_PD_EFFECT,
        precipitant_drug="fluconazole",
        object_drug="vortioxetine",
        effect_id="nausea",
        candidate_type=CANDIDATE_PD_SHARED_EFFECT,
    )
    aggregates = [
        AggregateConcern(
            aggregate_type=AGGREGATE_SHARED_PD_EFFECT,
            anchor="nausea",
            policy_concern=POLICY_TOLERABILITY_CONCERN,
            drugs=("fluconazole", "vortioxetine"),
            effect_id="nausea",
            members=(result,),
        )
    ]

    scored = policy_result_to_scored_concern(result, aggregates)

    assert scored.aggregate_member_count == 1
    assert scored.related_targets == ()
    assert scored.related_effects == ("nausea",)