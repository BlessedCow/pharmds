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
    POLICY_TOLERABILITY_CONCERN,
)
from core.mechanism_scoring import (
    CONFIDENCE_HIGH,
    CONFIDENCE_MODERATE,
    SEVERITY_UNSCORED,
    ScoredConcern,
)
from core.mechanism_scoring_debug import (
    format_scored_concern,
    format_scored_concerns,
)


def test_format_scored_concern_with_target():
    concern = ScoredConcern(
        policy_concern=POLICY_MECHANISTIC_CONCERN,
        source_concern=CONCERN_EXPOSURE_INCREASE,
        precipitant_drug="bupropion",
        object_drug="vortioxetine",
        target="CYP2D6",
        candidate_type=CANDIDATE_ENZYME_INHIBITION,
        confidence=CONFIDENCE_HIGH,
    )

    assert format_scored_concern(concern) == (
        "mechanistic_concern: bupropion -> vortioxetine via CYP2D6 "
        "| source_concern=exposure_increase "
        "| candidate_type=ENZYME_INHIBITION_EXPOSURE "
        f"| confidence={CONFIDENCE_HIGH} "
        f"| severity={SEVERITY_UNSCORED}"
    )


def test_format_scored_concern_with_effect_id():
    concern = ScoredConcern(
        policy_concern=POLICY_TOLERABILITY_CONCERN,
        source_concern=CONCERN_ADDITIVE_PD_EFFECT,
        precipitant_drug="fluconazole",
        object_drug="vortioxetine",
        effect_id="nausea",
        candidate_type=CANDIDATE_PD_SHARED_EFFECT,
        confidence=CONFIDENCE_MODERATE,
    )

    assert format_scored_concern(concern) == (
        "tolerability_concern: fluconazole + vortioxetine via nausea "
        "| source_concern=additive_pd_effect "
        "| candidate_type=PD_SHARED_EFFECT "
        f"| confidence={CONFIDENCE_MODERATE} "
        f"| severity={SEVERITY_UNSCORED}"
    )


def test_format_scored_concerns_formats_multiple():
    concerns = [
        ScoredConcern(
            policy_concern=POLICY_MECHANISTIC_CONCERN,
            source_concern=CONCERN_EXPOSURE_INCREASE,
            precipitant_drug="bupropion",
            object_drug="vortioxetine",
            target="CYP2D6",
            candidate_type=CANDIDATE_ENZYME_INHIBITION,
            confidence=CONFIDENCE_HIGH,
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
    ]

    assert format_scored_concerns(concerns) == [
        (
            "mechanistic_concern: bupropion -> vortioxetine via CYP2D6 "
            "| source_concern=exposure_increase "
            "| candidate_type=ENZYME_INHIBITION_EXPOSURE "
            f"| confidence={CONFIDENCE_HIGH} "
            f"| severity={SEVERITY_UNSCORED}"
        ),
        (
            "tolerability_concern: fluconazole + vortioxetine via nausea "
            "| source_concern=additive_pd_effect "
            "| candidate_type=PD_SHARED_EFFECT "
            f"| confidence={CONFIDENCE_MODERATE} "
            f"| severity={SEVERITY_UNSCORED}"
        ),
    ]