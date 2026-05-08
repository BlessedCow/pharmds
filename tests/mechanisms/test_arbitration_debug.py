from core.mechanisms.arbitration import (
    CONCERN_ADDITIVE_PD_EFFECT,
    CONCERN_EXPOSURE_INCREASE,
    CONFIDENCE_PLACEHOLDER,
    SEVERITY_PLACEHOLDER,
    ArbitrationResult,
)
from core.mechanisms.arbitration_debug import (
    format_arbitration_result,
    format_arbitration_results,
)
from core.mechanisms.candidates import (
    CANDIDATE_ENZYME_INHIBITION,
    CANDIDATE_PD_SHARED_EFFECT,
)


def test_format_arbitration_result_with_target():
    result = ArbitrationResult(
        candidate_type=CANDIDATE_ENZYME_INHIBITION,
        concern=CONCERN_EXPOSURE_INCREASE,
        precipitant_drug="bupropion",
        object_drug="vortioxetine",
        target="CYP2D6",
    )

    assert format_arbitration_result(result) == (
        "exposure_increase: bupropion -> vortioxetine via CYP2D6 "
        "| candidate_type=ENZYME_INHIBITION_EXPOSURE "
        f"| confidence={CONFIDENCE_PLACEHOLDER} "
        f"| severity={SEVERITY_PLACEHOLDER}"
    )


def test_format_arbitration_result_with_effect_id():
    result = ArbitrationResult(
        candidate_type=CANDIDATE_PD_SHARED_EFFECT,
        concern=CONCERN_ADDITIVE_PD_EFFECT,
        precipitant_drug="fluconazole",
        object_drug="vortioxetine",
        effect_id="nausea",
    )

    assert format_arbitration_result(result) == (
        "additive_pd_effect: fluconazole + vortioxetine via nausea "
        "| candidate_type=PD_SHARED_EFFECT "
        f"| confidence={CONFIDENCE_PLACEHOLDER} "
        f"| severity={SEVERITY_PLACEHOLDER}"
    )


def test_format_arbitration_results_formats_multiple():
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

    assert format_arbitration_results(results) == [
        (
            "exposure_increase: bupropion -> vortioxetine via CYP2D6 "
            "| candidate_type=ENZYME_INHIBITION_EXPOSURE "
            f"| confidence={CONFIDENCE_PLACEHOLDER} "
            f"| severity={SEVERITY_PLACEHOLDER}"
        ),
        (
            "additive_pd_effect: fluconazole + vortioxetine via nausea "
            "| candidate_type=PD_SHARED_EFFECT "
            f"| confidence={CONFIDENCE_PLACEHOLDER} "
            f"| severity={SEVERITY_PLACEHOLDER}"
        ),
    ]
