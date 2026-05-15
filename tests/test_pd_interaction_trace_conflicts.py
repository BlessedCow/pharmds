from core.evidence.pd_interaction_traces import (
    build_additive_pd_effect_evidence_trace,
)


def _claim(supports_claim):
    return {
        "claim_id": "claim_test_drug_pd_effect_nausea_001",
        "claim_type": "pd_effect",
        "subject": {
            "entity_type": "drug",
            "id": "test_drug",
        },
        "predicate": "has_pd_effect",
        "object": {
            "effect_id": "nausea",
        },
        "claim_status": "active",
        "review": {
            "status": "approved",
            "reviewed_by": "maintainer",
            "reviewed_at": "2026-05-13",
        },
        "evidence": [
            {
                "source_id": "source_internal_curated_pd_effects_v1",
                "evidence_type": "internal_curated_entry",
                "supports_claim": supports_claim,
                "confidence": "moderate",
                "notes": "Test evidence.",
            }
        ],
    }


def test_additive_pd_effect_trace_marks_overall_status_conflicting(monkeypatch):
    def fake_claims_for_drug_effect(drug_id, effect_id):
        if drug_id == "drug_a":
            return [_claim(True), _claim(False)]

        return [_claim(True)]

    monkeypatch.setattr(
        "core.evidence.traces."
        "get_approved_active_pd_effect_claims_for_drug_effect",
        fake_claims_for_drug_effect,
    )

    trace = build_additive_pd_effect_evidence_trace(
        ["drug_a", "drug_b"],
        "nausea",
    )

    assert trace["overall_evidence_status"] == "conflicting"
    assert trace["drugs"][0]["evidence_status"] == "conflicting"
    assert trace["drugs"][1]["evidence_status"] == "present"