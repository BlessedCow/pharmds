from core.evidence.completeness import (
    CONFIDENCE_HIGH,
    CONFIDENCE_LOW,
    CONFIDENCE_MODERATE,
    CONFIDENCE_NONE,
    COVERAGE_COMPLETE,
    COVERAGE_CONFLICTING,
    COVERAGE_DISPUTED,
    COVERAGE_MISSING,
    build_pd_effect_evidence_gap_report,
    summarize_pd_effect_claim_coverage,
)
from core.models import Facts, PDEffect


def _claim_trace(
    *,
    support_status="supported",
    confidence_level="moderate",
):
    return {
        "claim_id": "claim_test_drug_pd_effect_nausea_001",
        "claim_type": "pd_effect",
        "drug_id": "test_drug",
        "predicate": "has_pd_effect",
        "effect_id": "nausea",
        "claim_status": "active",
        "review": {
            "status": "approved",
            "reviewed_by": "maintainer",
            "reviewed_at": "2026-05-13",
        },
        "evidence_support_status": support_status,
        "evidence_support_counts": {
            "supporting": 1 if support_status == "supported" else 0,
            "disputing": 1 if support_status == "disputed" else 0,
        },
        "evidence_confidence": {
            "level": confidence_level,
            "score": 60,
            "reasons": ["test reason"],
        },
        "evidence": [],
    }


def test_summarize_pd_effect_claim_coverage_marks_missing(monkeypatch):
    monkeypatch.setattr(
        "core.evidence.completeness.build_pd_effect_traces_for_drug_effect",
        lambda drug_id, effect_id: [],
    )

    summary = summarize_pd_effect_claim_coverage(
        "test_drug",
        "nausea",
    )

    assert summary["coverage_status"] == COVERAGE_MISSING
    assert summary["confidence_status"] == CONFIDENCE_NONE
    assert summary["classification"] == COVERAGE_MISSING
    assert summary["claim_count"] == 0


def test_summarize_pd_effect_claim_coverage_marks_moderate_complete(
    monkeypatch,
):
    monkeypatch.setattr(
        "core.evidence.completeness.build_pd_effect_traces_for_drug_effect",
        lambda drug_id, effect_id: [_claim_trace()],
    )

    summary = summarize_pd_effect_claim_coverage(
        "test_drug",
        "nausea",
    )

    assert summary["coverage_status"] == COVERAGE_COMPLETE
    assert summary["confidence_level"] == "moderate"
    assert summary["confidence_status"] == CONFIDENCE_MODERATE
    assert summary["classification"] == CONFIDENCE_MODERATE
    assert summary["claim_count"] == 1


def test_summarize_pd_effect_claim_coverage_uses_highest_confidence(
    monkeypatch,
):
    monkeypatch.setattr(
        "core.evidence.completeness.build_pd_effect_traces_for_drug_effect",
        lambda drug_id, effect_id: [
            _claim_trace(confidence_level="low"),
            _claim_trace(confidence_level="high"),
        ],
    )

    summary = summarize_pd_effect_claim_coverage(
        "test_drug",
        "nausea",
    )

    assert summary["coverage_status"] == COVERAGE_COMPLETE
    assert summary["confidence_status"] == CONFIDENCE_HIGH
    assert summary["classification"] == CONFIDENCE_HIGH


def test_summarize_pd_effect_claim_coverage_marks_disputed(monkeypatch):
    monkeypatch.setattr(
        "core.evidence.completeness.build_pd_effect_traces_for_drug_effect",
        lambda drug_id, effect_id: [
            _claim_trace(
                support_status="disputed",
                confidence_level="low",
            )
        ],
    )

    summary = summarize_pd_effect_claim_coverage(
        "test_drug",
        "nausea",
    )

    assert summary["coverage_status"] == COVERAGE_DISPUTED
    assert summary["classification"] == COVERAGE_DISPUTED


def test_summarize_pd_effect_claim_coverage_marks_conflicting(monkeypatch):
    monkeypatch.setattr(
        "core.evidence.completeness.build_pd_effect_traces_for_drug_effect",
        lambda drug_id, effect_id: [
            _claim_trace(support_status="supported"),
            _claim_trace(support_status="disputed"),
        ],
    )

    summary = summarize_pd_effect_claim_coverage(
        "test_drug",
        "nausea",
    )

    assert summary["coverage_status"] == COVERAGE_CONFLICTING
    assert summary["classification"] == COVERAGE_CONFLICTING


def test_build_pd_effect_evidence_gap_report_counts_classifications(
    monkeypatch,
):
    facts = Facts(
    pd_effects={
        "drug_a": [
            PDEffect(
                effect_id="nausea",
                direction="increase",
                magnitude="medium",
            ),
            PDEffect(
                effect_id="sedation",
                direction="increase",
                magnitude="medium",
            ),
        ],
        "drug_b": [
            PDEffect(
                effect_id="nausea",
                direction="increase",
                magnitude="medium",
            ),
        ],
    },
)

    def fake_traces(drug_id, effect_id):
        if drug_id == "drug_a" and effect_id == "nausea":
            return [_claim_trace(confidence_level="moderate")]

        if drug_id == "drug_a" and effect_id == "sedation":
            return []

        return [_claim_trace(confidence_level="low")]

    monkeypatch.setattr(
        "core.evidence.completeness.build_pd_effect_traces_for_drug_effect",
        fake_traces,
    )

    report = build_pd_effect_evidence_gap_report(facts)

    assert report["report_type"] == "pd_effect_evidence_gap_report"
    assert report["total_pd_effects"] == 3
    assert report["classification_counts"] == {
        CONFIDENCE_LOW: 1,
        CONFIDENCE_MODERATE: 1,
        COVERAGE_MISSING: 1,
    }
    assert report["coverage_counts"] == {
        COVERAGE_COMPLETE: 2,
        COVERAGE_MISSING: 1,
    }
    assert report["confidence_counts"] == {
        CONFIDENCE_LOW: 1,
        CONFIDENCE_MODERATE: 1,
        CONFIDENCE_NONE: 1,
    }