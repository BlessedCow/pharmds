from core.evidence.traces import (
    build_pd_effect_claim_trace,
    build_pd_effect_traces_for_drug,
    build_pd_effect_traces_for_drug_effect,
    build_source_trace,
    has_approved_active_pd_effect_evidence,
)


def test_build_source_trace_returns_source_metadata():
    trace = build_source_trace("source_internal_curated_pd_effects_v1")

    assert trace == {
        "source_id": "source_internal_curated_pd_effects_v1",
        "found": True,
        "title": "Internal curated pharmacodynamic effects dataset",
        "source_type": "internal_curated_entry",
        "publisher": "PharmDS",
        "url": None,
        "reliability_tier": "curated",
    }


def test_build_source_trace_handles_missing_source():
    trace = build_source_trace("source_missing")

    assert trace == {
        "source_id": "source_missing",
        "found": False,
        "title": None,
        "source_type": None,
        "publisher": None,
        "url": None,
        "reliability_tier": None,
    }


def test_build_pd_effect_claim_trace_returns_expected_shape():
    claim = {
        "claim_id": "claim_example_pd_effect_nausea_001",
        "claim_type": "pd_effect",
        "subject": {
            "entity_type": "drug",
            "id": "example_drug",
        },
        "predicate": "has_pd_effect",
        "object": {
            "effect_id": "nausea",
        },
        "evidence": [
            {
                "source_id": "source_internal_curated_pd_effects_v1",
                "evidence_type": "internal_curated_entry",
                "supports_claim": True,
                "confidence": "moderate",
                "notes": "Example note.",
            }
        ],
        "review": {
            "status": "approved",
            "reviewed_by": "maintainer",
            "reviewed_at": None,
        },
        "claim_status": "active",
    }

    trace = build_pd_effect_claim_trace(claim)

    assert trace["claim_id"] == "claim_example_pd_effect_nausea_001"
    assert trace["claim_type"] == "pd_effect"
    assert trace["drug_id"] == "example_drug"
    assert trace["predicate"] == "has_pd_effect"
    assert trace["effect_id"] == "nausea"
    assert trace["claim_status"] == "active"
    assert trace["review"]["status"] == "approved"

    assert len(trace["evidence"]) == 1
    evidence = trace["evidence"][0]

    assert evidence["evidence_type"] == "internal_curated_entry"
    assert evidence["supports_claim"] is True
    assert evidence["confidence"] == "moderate"
    assert evidence["notes"] == "Example note."
    assert evidence["source"]["source_id"] == "source_internal_curated_pd_effects_v1"
    assert evidence["source"]["found"] is True


def test_build_pd_effect_traces_for_drug_effect_returns_matching_trace():
    traces = build_pd_effect_traces_for_drug_effect(
        "clarithromycin",
        "nausea",
    )

    assert len(traces) == 1

    trace = traces[0]

    assert trace["claim_id"] == "claim_clarithromycin_pd_effect_nausea_001"
    assert trace["drug_id"] == "clarithromycin"
    assert trace["effect_id"] == "nausea"
    assert trace["review"]["status"] == "approved"
    assert trace["claim_status"] == "active"

    assert trace["evidence"][0]["confidence"] == "moderate"
    assert (
        trace["evidence"][0]["source"]["source_id"]
        == "source_internal_curated_pd_effects_v1"
    )


def test_build_pd_effect_traces_for_drug_effect_returns_empty_for_mismatch():
    traces = build_pd_effect_traces_for_drug_effect(
        "clarithromycin",
        "sedation",
    )

    assert traces == []


def test_build_pd_effect_traces_for_drug_returns_matching_traces():
    traces = build_pd_effect_traces_for_drug("fluconazole")

    claim_ids = {trace["claim_id"] for trace in traces}

    assert "claim_fluconazole_pd_effect_nausea_001" in claim_ids


def test_has_approved_active_pd_effect_evidence_returns_true_for_known_claim():
    result = has_approved_active_pd_effect_evidence(
        "fluconazole",
        "nausea",
    )

    assert result is True


def test_has_approved_active_pd_effect_evidence_returns_false_for_missing_claim():
    result = has_approved_active_pd_effect_evidence(
        "fluconazole",
        "sedation",
    )

    assert result is False
    
def test_build_pd_effect_traces_for_drug_returns_expanded_pd_claims():
    traces = build_pd_effect_traces_for_drug("alprazolam")

    claim_ids = {trace["claim_id"] for trace in traces}

    assert "claim_alprazolam_pd_effect_sedation_001" in claim_ids
    assert "claim_alprazolam_pd_effect_cns_depression_001" in claim_ids
    
def test_has_approved_active_pd_effect_evidence_returns_true_for_expanded_claim():
    result = has_approved_active_pd_effect_evidence(
        "clonazepam",
        "sedation",
    )

    assert result is True
    
