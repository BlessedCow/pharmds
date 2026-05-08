from core.mechanism_arbitration import (
    CONCERN_ADDITIVE_PD_EFFECT,
    CONCERN_EXPOSURE_DECREASE,
    CONCERN_EXPOSURE_INCREASE,
    ArbitrationResult,
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
    POLICY_UNKNOWN_CONCERN,
    ConcernPolicyResult,
    apply_concern_policy,
    arbitration_result_to_policy_result,
    dedupe_policy_results,
)


def test_policy_maps_exposure_increase_to_mechanistic_concern():
    result = ArbitrationResult(
        candidate_type=CANDIDATE_ENZYME_INHIBITION,
        concern=CONCERN_EXPOSURE_INCREASE,
        precipitant_drug="bupropion",
        object_drug="vortioxetine",
        target="CYP2D6",
    )

    policy = arbitration_result_to_policy_result(result)

    assert policy.policy_concern == POLICY_MECHANISTIC_CONCERN
    assert policy.source_concern == CONCERN_EXPOSURE_INCREASE
    assert policy.precipitant_drug == "bupropion"
    assert policy.object_drug == "vortioxetine"
    assert policy.target == "CYP2D6"
    assert policy.effect_id is None


def test_policy_maps_exposure_decrease_to_exposure_reduction_concern():
    result = ArbitrationResult(
        candidate_type=CANDIDATE_ENZYME_INDUCTION,
        concern=CONCERN_EXPOSURE_DECREASE,
        precipitant_drug="rifampin",
        object_drug="vortioxetine",
        target="CYP3A4",
    )

    policy = arbitration_result_to_policy_result(result)

    assert policy.policy_concern == POLICY_EXPOSURE_REDUCTION_CONCERN
    assert policy.source_concern == CONCERN_EXPOSURE_DECREASE
    assert policy.precipitant_drug == "rifampin"
    assert policy.object_drug == "vortioxetine"
    assert policy.target == "CYP3A4"


def test_policy_maps_shared_nausea_to_tolerability_concern():
    result = ArbitrationResult(
        candidate_type=CANDIDATE_PD_SHARED_EFFECT,
        concern=CONCERN_ADDITIVE_PD_EFFECT,
        precipitant_drug="fluconazole",
        object_drug="vortioxetine",
        effect_id="nausea",
    )

    policy = arbitration_result_to_policy_result(result)

    assert policy.policy_concern == POLICY_TOLERABILITY_CONCERN
    assert policy.source_concern == CONCERN_ADDITIVE_PD_EFFECT
    assert policy.effect_id == "nausea"


def test_policy_maps_shared_qt_to_safety_concern():
    result = ArbitrationResult(
        candidate_type=CANDIDATE_PD_SHARED_EFFECT,
        concern=CONCERN_ADDITIVE_PD_EFFECT,
        precipitant_drug="clarithromycin",
        object_drug="fluconazole",
        effect_id="QT_prolongation",
    )

    policy = arbitration_result_to_policy_result(result)

    assert policy.policy_concern == POLICY_SAFETY_CONCERN
    assert policy.source_concern == CONCERN_ADDITIVE_PD_EFFECT
    assert policy.effect_id == "QT_prolongation"


def test_policy_maps_unknown_pd_effect_to_unknown_concern():
    result = ArbitrationResult(
        candidate_type=CANDIDATE_PD_SHARED_EFFECT,
        concern=CONCERN_ADDITIVE_PD_EFFECT,
        precipitant_drug="drug_a",
        object_drug="drug_b",
        effect_id="uncategorized_effect",
    )

    policy = arbitration_result_to_policy_result(result)

    assert policy.policy_concern == POLICY_UNKNOWN_CONCERN
    assert policy.effect_id == "uncategorized_effect"


def test_apply_concern_policy_maps_multiple_results():
    results = [
        ArbitrationResult(
            candidate_type=CANDIDATE_ENZYME_INHIBITION,
            concern=CONCERN_EXPOSURE_INCREASE,
            precipitant_drug="bupropion",
            object_drug="vortioxetine",
            target="CYP2D6",
        ),
        ArbitrationResult(
            candidate_type=CANDIDATE_PD_SHARED_EFFECT,
            concern=CONCERN_ADDITIVE_PD_EFFECT,
            precipitant_drug="fluconazole",
            object_drug="vortioxetine",
            effect_id="nausea",
        ),
    ]

    policy_results = apply_concern_policy(results)

    assert len(policy_results) == 2
    assert policy_results[0].policy_concern == POLICY_MECHANISTIC_CONCERN
    assert policy_results[1].policy_concern == POLICY_TOLERABILITY_CONCERN


def test_dedupe_policy_results_preserves_first_seen_order():
    results = [
        ConcernPolicyResult(
            policy_concern=POLICY_TOLERABILITY_CONCERN,
            source_concern=CONCERN_ADDITIVE_PD_EFFECT,
            precipitant_drug="fluconazole",
            object_drug="vortioxetine",
            effect_id="nausea",
        ),
        ConcernPolicyResult(
            policy_concern=POLICY_TOLERABILITY_CONCERN,
            source_concern=CONCERN_ADDITIVE_PD_EFFECT,
            precipitant_drug="fluconazole",
            object_drug="vortioxetine",
            effect_id="nausea",
        ),
        ConcernPolicyResult(
            policy_concern=POLICY_SAFETY_CONCERN,
            source_concern=CONCERN_ADDITIVE_PD_EFFECT,
            precipitant_drug="clarithromycin",
            object_drug="fluconazole",
            effect_id="QT_prolongation",
        ),
    ]

    deduped = dedupe_policy_results(results)

    assert len(deduped) == 2
    assert deduped[0].precipitant_drug == "fluconazole"
    assert deduped[1].precipitant_drug == "clarithromycin"