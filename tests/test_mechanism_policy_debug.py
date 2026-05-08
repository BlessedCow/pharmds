from core.mechanism_arbitration import (
    CONCERN_ADDITIVE_PD_EFFECT,
    CONCERN_EXPOSURE_INCREASE,
    CONFIDENCE_PLACEHOLDER,
    SEVERITY_PLACEHOLDER,
)
from core.mechanism_candidates import (
    CANDIDATE_ENZYME_INHIBITION,
    CANDIDATE_PD_SHARED_EFFECT,
)
from core.mechanism_policy import (
    POLICY_MECHANISTIC_CONCERN,
    POLICY_TOLERABILITY_CONCERN,
    ConcernPolicyResult,
)
from core.mechanism_policy_debug import (
    format_policy_result,
    format_policy_results,
)


def test_format_policy_result_with_target():
    result = ConcernPolicyResult(
        policy_concern=POLICY_MECHANISTIC_CONCERN,
        source_concern=CONCERN_EXPOSURE_INCREASE,
        precipitant_drug="bupropion",
        object_drug="vortioxetine",
        target="CYP2D6",
        candidate_type=CANDIDATE_ENZYME_INHIBITION,
    )

    assert format_policy_result(result) == (
        "mechanistic_concern: bupropion -> vortioxetine via CYP2D6 "
        "| source_concern=exposure_increase "
        "| candidate_type=ENZYME_INHIBITION_EXPOSURE "
        f"| confidence={CONFIDENCE_PLACEHOLDER} "
        f"| severity={SEVERITY_PLACEHOLDER}"
    )


def test_format_policy_result_with_effect_id():
    result = ConcernPolicyResult(
        policy_concern=POLICY_TOLERABILITY_CONCERN,
        source_concern=CONCERN_ADDITIVE_PD_EFFECT,
        precipitant_drug="fluconazole",
        object_drug="vortioxetine",
        effect_id="nausea",
        candidate_type=CANDIDATE_PD_SHARED_EFFECT,
    )

    assert format_policy_result(result) == (
        "tolerability_concern: fluconazole + vortioxetine via nausea "
        "| source_concern=additive_pd_effect "
        "| candidate_type=PD_SHARED_EFFECT "
        f"| confidence={CONFIDENCE_PLACEHOLDER} "
        f"| severity={SEVERITY_PLACEHOLDER}"
    )


def test_format_policy_results_formats_multiple():
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

    assert format_policy_results(results) == [
        (
            "mechanistic_concern: bupropion -> vortioxetine via CYP2D6 "
            "| source_concern=exposure_increase "
            "| candidate_type=ENZYME_INHIBITION_EXPOSURE "
            f"| confidence={CONFIDENCE_PLACEHOLDER} "
            f"| severity={SEVERITY_PLACEHOLDER}"
        ),
        (
            "tolerability_concern: fluconazole + vortioxetine via nausea "
            "| source_concern=additive_pd_effect "
            "| candidate_type=PD_SHARED_EFFECT "
            f"| confidence={CONFIDENCE_PLACEHOLDER} "
            f"| severity={SEVERITY_PLACEHOLDER}"
        ),
    ]