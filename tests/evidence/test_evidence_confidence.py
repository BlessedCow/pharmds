from core.evidence.confidence import (
    CONFIDENCE_HIGH,
    CONFIDENCE_LOW,
    CONFIDENCE_MODERATE,
    CONFIDENCE_UNCERTAIN,
    clamp_confidence_score,
    confidence_level_for_score,
    synthesize_claim_confidence,
)


def _claim_trace(
    *,
    supports_claim=True,
    evidence_type="internal_curated_entry",
    manual_confidence="moderate",
    reliability_tier="curated",
    review_status="approved",
    claim_status="active",
    evidence_support_status="supported",
):
    return {
        "claim_id": "claim_test_drug_pd_effect_nausea_001",
        "claim_type": "pd_effect",
        "drug_id": "test_drug",
        "predicate": "has_pd_effect",
        "effect_id": "nausea",
        "claim_status": claim_status,
        "review": {
            "status": review_status,
            "reviewed_by": "maintainer",
            "reviewed_at": "2026-05-13",
        },
        "evidence_support_status": evidence_support_status,
        "evidence_support_counts": {
            "supporting": 1 if supports_claim is True else 0,
            "disputing": 1 if supports_claim is False else 0,
        },
        "evidence": [
            {
                "source": {
                    "source_id": "source_internal_curated_pd_effects_v1",
                    "found": True,
                    "title": "Internal curated pharmacodynamic effects dataset",
                    "source_type": "internal_curated_entry",
                    "publisher": "PharmDS",
                    "url": None,
                    "reliability_tier": reliability_tier,
                },
                "evidence_type": evidence_type,
                "supports_claim": supports_claim,
                "confidence": manual_confidence,
                "notes": "Test evidence.",
            }
        ],
    }


def test_clamp_confidence_score_keeps_score_between_zero_and_one_hundred():
    assert clamp_confidence_score(-10) == 0
    assert clamp_confidence_score(50) == 50
    assert clamp_confidence_score(150) == 100


def test_confidence_level_for_score_maps_scores_to_levels():
    assert confidence_level_for_score(90) == CONFIDENCE_HIGH
    assert confidence_level_for_score(60) == CONFIDENCE_MODERATE
    assert confidence_level_for_score(30) == CONFIDENCE_UNCERTAIN
    assert confidence_level_for_score(10) == CONFIDENCE_LOW


def test_synthesize_claim_confidence_returns_high_for_strong_claim():
    confidence = synthesize_claim_confidence(_claim_trace(
        evidence_type="drug_label",
        manual_confidence="high",
        reliability_tier="high",
    ))

    assert confidence["level"] == "high"
    assert confidence["score"] >= 75
    assert "approved review" in confidence["reasons"]
    assert "supporting evidence present" in confidence["reasons"]


def test_synthesize_claim_confidence_returns_moderate_for_curated_claim():
    confidence = synthesize_claim_confidence(_claim_trace())

    assert confidence["level"] == "moderate"
    assert 50 <= confidence["score"] < 75
    assert "internal_curated_entry evidence" in confidence["reasons"]
    assert "source reliability=curated" in confidence["reasons"]


def test_synthesize_claim_confidence_penalizes_disputing_evidence():
    confidence = synthesize_claim_confidence(_claim_trace(
        supports_claim=False,
        evidence_support_status="disputed",
    ))

    assert confidence["level"] in {"low", "uncertain"}
    assert "disputed evidence" in confidence["reasons"]
    assert "disputing evidence present" in confidence["reasons"]


def test_synthesize_claim_confidence_penalizes_conflicting_evidence():
    trace = _claim_trace(evidence_support_status="conflicting")
    trace["evidence"].append(
        {
            "source": {
                "source_id": "source_example_dispute",
                "found": True,
                "title": "Example disputing source",
                "source_type": "case_report",
                "publisher": "Example",
                "url": None,
                "reliability_tier": "low",
            },
            "evidence_type": "case_report",
            "supports_claim": False,
            "confidence": "low",
            "notes": "Example disputing evidence.",
        }
    )

    confidence = synthesize_claim_confidence(trace)

    assert confidence["level"] in {"low", "uncertain", "moderate"}
    assert "conflicting evidence" in confidence["reasons"]
    assert "disputing evidence present" in confidence["reasons"]


def test_synthesize_claim_confidence_penalizes_missing_evidence():
    trace = _claim_trace()
    trace["evidence"] = []
    trace["evidence_support_status"] = "undetermined"
    trace["evidence_support_counts"] = {
        "supporting": 0,
        "disputing": 0,
    }

    confidence = synthesize_claim_confidence(trace)

    assert confidence["level"] in {"low", "uncertain"}
    assert "no evidence items" in confidence["reasons"]
    assert "evidence support undetermined" in confidence["reasons"]