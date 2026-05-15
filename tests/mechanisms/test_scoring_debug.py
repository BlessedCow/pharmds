from core.mechanisms.arbitration import (
    CONCERN_ADDITIVE_PD_EFFECT,
    CONCERN_EXPOSURE_INCREASE,
)
from core.mechanisms.candidates import (
    CANDIDATE_ENZYME_INHIBITION,
    CANDIDATE_PD_SHARED_EFFECT,
)
from core.mechanisms.policy import (
    POLICY_MECHANISTIC_CONCERN,
    POLICY_TOLERABILITY_CONCERN,
)
from core.mechanisms.scoring import (
    CONFIDENCE_HIGH,
    CONFIDENCE_MODERATE,
    SEVERITY_UNSCORED,
    ScoredConcern,
)
from core.mechanisms.scoring_debug import (
    _format_debug_evidence_trace,
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


def es_aggregate_contexttest_format_scored_concern_includ():
    concern = ScoredConcern(
        policy_concern=POLICY_MECHANISTIC_CONCERN,
        source_concern=CONCERN_EXPOSURE_INCREASE,
        precipitant_drug="bupropion",
        object_drug="vortioxetine",
        target="CYP2D6",
        candidate_type=CANDIDATE_ENZYME_INHIBITION,
        confidence=CONFIDENCE_HIGH,
        aggregate_member_count=3,
        related_targets=("CYP2C19", "CYP2C9", "CYP2D6"),
    )

    assert format_scored_concern(concern) == (
        "mechanistic_concern: bupropion -> vortioxetine via CYP2D6 "
        "| source_concern=exposure_increase "
        "| candidate_type=ENZYME_INHIBITION_EXPOSURE "
        f"| confidence={CONFIDENCE_HIGH} "
        f"| severity={SEVERITY_UNSCORED} "
        "| aggregate_members=3 "
        "| related_targets=CYP2C19, CYP2C9, CYP2D6"
    )


def test_format_evidence_trace_for_debug():
    trace = {
        "trace_type": "additive_pd_effect",
        "effect_id": "nausea",
        "drug_ids": ["clarithromycin", "fluconazole"],
        "overall_evidence_status": "complete",
        "drugs": [
            {
                "drug_id": "clarithromycin",
                "effect_id": "nausea",
                "evidence_status": "present",
                "claims": [
                    {
                        "claim_id": (
                            "claim_clarithromycin_pd_effect_nausea_001"
                        ),
                        "claim_type": "pd_effect",
                        "drug_id": "clarithromycin",
                        "predicate": "has_pd_effect",
                        "effect_id": "nausea",
                        "claim_status": "active",
                        "review": {
                            "status": "approved",
                        },
                        "evidence": [
                            {
                                "source": {
                                    "source_id": (
                                        "source_internal_curated_pd_effects_v1"
                                    ),
                                    "found": True,
                                    "title": (
                                        "Internal curated pharmacodynamic "
                                        "effects dataset"
                                    ),
                                    "source_type": "internal_curated_entry",
                                    "publisher": "PharmDS",
                                    "url": None,
                                    "reliability_tier": "curated",
                                },
                                "evidence_type": "internal_curated_entry",
                                "confidence": "moderate",
                            }
                        ],
                    }
                ],
            },
            {
                "drug_id": "fluconazole",
                "effect_id": "nausea",
                "evidence_status": "present",
                "claims": [
                    {
                        "claim_id": "claim_fluconazole_pd_effect_nausea_001",
                        "claim_type": "pd_effect",
                        "drug_id": "fluconazole",
                        "predicate": "has_pd_effect",
                        "effect_id": "nausea",
                        "claim_status": "active",
                        "review": {
                            "status": "approved",
                        },
                        "evidence": [
                            {
                                "source": {
                                    "source_id": (
                                        "source_internal_curated_pd_effects_v1"
                                    ),
                                    "found": True,
                                    "title": (
                                        "Internal curated pharmacodynamic "
                                        "effects dataset"
                                    ),
                                    "source_type": "internal_curated_entry",
                                    "publisher": "PharmDS",
                                    "url": None,
                                    "reliability_tier": "curated",
                                },
                                "evidence_type": "internal_curated_entry",
                                "confidence": "moderate",
                            }
                        ],
                    }
                ],
            },
        ],
    }

    assert _format_debug_evidence_trace(trace) == [
        "Evidence:",
        "  Evidence status for nausea: complete",
        (
            "  clarithromycin evidence_status=present; "
            "clarithromycin -> nausea: pd_effect; "
            "claim_status=active; review_status=approved; "
            "evidence=Internal curated pharmacodynamic effects dataset "
            "(PharmDS, curated); "
            "evidence_type=internal_curated_entry; confidence=moderate"
        ),
        (
            "  fluconazole evidence_status=present; "
            "fluconazole -> nausea: pd_effect; "
            "claim_status=active; review_status=approved; "
            "evidence=Internal curated pharmacodynamic effects dataset "
            "(PharmDS, curated); "
            "evidence_type=internal_curated_entry; confidence=moderate"
        ),
    ]

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
def test_format_debug_evidence_trace():
    trace = {
        "trace_type": "additive_pd_effect",
        "effect_id": "nausea",
        "drug_ids": ["clarithromycin", "fluconazole"],
        "overall_evidence_status": "complete",
        "drugs": [
            {
                "drug_id": "clarithromycin",
                "effect_id": "nausea",
                "evidence_status": "present",
                "claims": [
                    {
                        "claim_id": (
                            "claim_clarithromycin_pd_effect_nausea_001"
                        ),
                        "claim_type": "pd_effect",
                        "drug_id": "clarithromycin",
                        "predicate": "has_pd_effect",
                        "effect_id": "nausea",
                        "claim_status": "active",
                        "review": {
                            "status": "approved",
                        },
                        "evidence": [
                            {
                                "source": {
                                    "source_id": (
                                        "source_internal_curated_pd_effects_v1"
                                    ),
                                    "found": True,
                                    "title": (
                                        "Internal curated pharmacodynamic "
                                        "effects dataset"
                                    ),
                                    "source_type": "internal_curated_entry",
                                    "publisher": "PharmDS",
                                    "url": None,
                                    "reliability_tier": "curated",
                                },
                                "evidence_type": "internal_curated_entry",
                                "confidence": "moderate",
                            }
                        ],
                    }
                ],
            },
            {
                "drug_id": "fluconazole",
                "effect_id": "nausea",
                "evidence_status": "present",
                "claims": [
                    {
                        "claim_id": "claim_fluconazole_pd_effect_nausea_001",
                        "claim_type": "pd_effect",
                        "drug_id": "fluconazole",
                        "predicate": "has_pd_effect",
                        "effect_id": "nausea",
                        "claim_status": "active",
                        "review": {
                            "status": "approved",
                        },
                        "evidence": [
                            {
                                "source": {
                                    "source_id": (
                                        "source_internal_curated_pd_effects_v1"
                                    ),
                                    "found": True,
                                    "title": (
                                        "Internal curated pharmacodynamic "
                                        "effects dataset"
                                    ),
                                    "source_type": "internal_curated_entry",
                                    "publisher": "PharmDS",
                                    "url": None,
                                    "reliability_tier": "curated",
                                },
                                "evidence_type": "internal_curated_entry",
                                "confidence": "moderate",
                            }
                        ],
                    }
                ],
            },
        ],
    }

    assert _format_debug_evidence_trace(trace) == [
        "Evidence:",
        "  Evidence status for nausea: complete",
        (
            "  clarithromycin evidence_status=present; "
            "clarithromycin -> nausea: pd_effect; "
            "claim_status=active; review_status=approved; "
            "evidence=Internal curated pharmacodynamic effects dataset "
            "(PharmDS, curated); "
            "evidence_type=internal_curated_entry; confidence=moderate"
        ),
        (
            "  fluconazole evidence_status=present; "
            "fluconazole -> nausea: pd_effect; "
            "claim_status=active; review_status=approved; "
            "evidence=Internal curated pharmacodynamic effects dataset "
            "(PharmDS, curated); "
            "evidence_type=internal_curated_entry; confidence=moderate"
        ),
    ]