from core.evidence.conflicts import (
    EVIDENCE_SUPPORT_CONFLICTING,
    EVIDENCE_SUPPORT_DISPUTED,
    EVIDENCE_SUPPORT_SUPPORTED,
    EVIDENCE_SUPPORT_UNDETERMINED,
    claim_has_disputing_evidence,
    claim_has_supporting_evidence,
    classify_evidence_support,
    count_evidence_support,
)
from core.evidence.traces import build_pd_effect_claim_trace


def _claim(evidence):
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
        "evidence": evidence,
    }


def _evidence(supports_claim):
    return {
        "source_id": "source_internal_curated_pd_effects_v1",
        "evidence_type": "internal_curated_entry",
        "supports_claim": supports_claim,
        "confidence": "moderate",
        "notes": "Test evidence.",
    }


def test_count_evidence_support_counts_supporting_and_disputing_items():
    evidence_items = [
        _evidence(True),
        _evidence(False),
        _evidence(True),
    ]

    assert count_evidence_support(evidence_items) == {
        "supporting": 2,
        "disputing": 1,
    }


def test_classify_evidence_support_detects_supported_claim():
    assert classify_evidence_support([_evidence(True)]) == (
        EVIDENCE_SUPPORT_SUPPORTED
    )


def test_classify_evidence_support_detects_disputed_claim():
    assert classify_evidence_support([_evidence(False)]) == (
        EVIDENCE_SUPPORT_DISPUTED
    )


def test_classify_evidence_support_detects_conflicting_claim():
    assert classify_evidence_support([
        _evidence(True),
        _evidence(False),
    ]) == EVIDENCE_SUPPORT_CONFLICTING


def test_classify_evidence_support_detects_undetermined_claim():
    assert classify_evidence_support([]) == EVIDENCE_SUPPORT_UNDETERMINED


def test_claim_support_helpers_detect_support_and_dispute():
    claim = _claim([
        _evidence(True),
        _evidence(False),
    ])

    assert claim_has_supporting_evidence(claim) is True
    assert claim_has_disputing_evidence(claim) is True


def test_build_pd_effect_claim_trace_includes_conflict_metadata():
    trace = build_pd_effect_claim_trace(_claim([
        _evidence(True),
        _evidence(False),
    ]))

    assert trace["evidence_support_status"] == "conflicting"
    assert trace["evidence_support_counts"] == {
        "supporting": 1,
        "disputing": 1,
    }