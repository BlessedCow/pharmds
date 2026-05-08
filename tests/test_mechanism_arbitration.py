from core.mechanism_arbitration import (
    CONCERN_ADDITIVE_PD_EFFECT,
    CONCERN_EXPOSURE_DECREASE,
    CONCERN_EXPOSURE_INCREASE,
    CONFIDENCE_PLACEHOLDER,
    SEVERITY_PLACEHOLDER,
    ArbitrationResult,
    arbitrate_candidates,
    candidate_to_arbitration_result,
    dedupe_arbitration_results,
)
from core.mechanism_candidates import (
    CANDIDATE_ENZYME_INDUCTION,
    CANDIDATE_ENZYME_INHIBITION,
    CANDIDATE_PD_SHARED_EFFECT,
    CANDIDATE_TRANSPORTER_INDUCTION,
    CANDIDATE_TRANSPORTER_INHIBITION,
    InteractionCandidate,
)


def test_candidate_to_arbitration_result_maps_enzyme_inhibition():
    candidate = InteractionCandidate(
        candidate_type=CANDIDATE_ENZYME_INHIBITION,
        precipitant_drug="bupropion",
        object_drug="vortioxetine",
        target="CYP2D6",
        explanation=(
            "bupropion inhibits CYP2D6; vortioxetine is a CYP2D6 substrate."
        ),
    )

    result = candidate_to_arbitration_result(candidate)

    assert result.candidate_type == CANDIDATE_ENZYME_INHIBITION
    assert result.concern == CONCERN_EXPOSURE_INCREASE
    assert result.precipitant_drug == "bupropion"
    assert result.object_drug == "vortioxetine"
    assert result.target == "CYP2D6"
    assert result.effect_id is None
    assert result.confidence == CONFIDENCE_PLACEHOLDER
    assert result.severity == SEVERITY_PLACEHOLDER
    assert result.explanation == candidate.explanation


def test_candidate_to_arbitration_result_maps_enzyme_induction():
    candidate = InteractionCandidate(
        candidate_type=CANDIDATE_ENZYME_INDUCTION,
        precipitant_drug="rifampin",
        object_drug="vortioxetine",
        target="CYP3A4",
    )

    result = candidate_to_arbitration_result(candidate)

    assert result.concern == CONCERN_EXPOSURE_DECREASE
    assert result.precipitant_drug == "rifampin"
    assert result.object_drug == "vortioxetine"
    assert result.target == "CYP3A4"


def test_candidate_to_arbitration_result_maps_transporter_inhibition():
    candidate = InteractionCandidate(
        candidate_type=CANDIDATE_TRANSPORTER_INHIBITION,
        precipitant_drug="clarithromycin",
        object_drug="digoxin",
        target="P-gp",
    )

    result = candidate_to_arbitration_result(candidate)

    assert result.concern == CONCERN_EXPOSURE_INCREASE
    assert result.precipitant_drug == "clarithromycin"
    assert result.object_drug == "digoxin"
    assert result.target == "P-gp"


def test_candidate_to_arbitration_result_maps_transporter_induction():
    candidate = InteractionCandidate(
        candidate_type=CANDIDATE_TRANSPORTER_INDUCTION,
        precipitant_drug="rifampin",
        object_drug="digoxin",
        target="P-gp",
    )

    result = candidate_to_arbitration_result(candidate)

    assert result.concern == CONCERN_EXPOSURE_DECREASE
    assert result.precipitant_drug == "rifampin"
    assert result.object_drug == "digoxin"
    assert result.target == "P-gp"


def test_candidate_to_arbitration_result_maps_shared_pd_effect():
    candidate = InteractionCandidate(
        candidate_type=CANDIDATE_PD_SHARED_EFFECT,
        precipitant_drug="fluconazole",
        object_drug="vortioxetine",
        effect_id="nausea",
    )

    result = candidate_to_arbitration_result(candidate)

    assert result.concern == CONCERN_ADDITIVE_PD_EFFECT
    assert result.precipitant_drug == "fluconazole"
    assert result.object_drug == "vortioxetine"
    assert result.effect_id == "nausea"
    assert result.target is None


def test_arbitrate_candidates_maps_multiple_candidates():
    candidates = [
        InteractionCandidate(
            candidate_type=CANDIDATE_ENZYME_INHIBITION,
            precipitant_drug="bupropion",
            object_drug="vortioxetine",
            target="CYP2D6",
        ),
        InteractionCandidate(
            candidate_type=CANDIDATE_PD_SHARED_EFFECT,
            precipitant_drug="fluconazole",
            object_drug="vortioxetine",
            effect_id="nausea",
        ),
    ]

    results = arbitrate_candidates(candidates)

    assert len(results) == 2
    assert results[0].concern == CONCERN_EXPOSURE_INCREASE
    assert results[1].concern == CONCERN_ADDITIVE_PD_EFFECT


def test_dedupe_arbitration_results_preserves_first_seen_order():
    results = [
        ArbitrationResult(
            candidate_type=CANDIDATE_PD_SHARED_EFFECT,
            concern=CONCERN_ADDITIVE_PD_EFFECT,
            precipitant_drug="fluconazole",
            object_drug="vortioxetine",
            effect_id="nausea",
        ),
        ArbitrationResult(
            candidate_type=CANDIDATE_PD_SHARED_EFFECT,
            concern=CONCERN_ADDITIVE_PD_EFFECT,
            precipitant_drug="fluconazole",
            object_drug="vortioxetine",
            effect_id="nausea",
        ),
        ArbitrationResult(
            candidate_type=CANDIDATE_PD_SHARED_EFFECT,
            concern=CONCERN_ADDITIVE_PD_EFFECT,
            precipitant_drug="clarithromycin",
            object_drug="vortioxetine",
            effect_id="nausea",
        ),
    ]

    deduped = dedupe_arbitration_results(results)

    assert len(deduped) == 2
    assert deduped[0].precipitant_drug == "fluconazole"
    assert deduped[1].precipitant_drug == "clarithromycin"