from core.evidence.completeness import (
    BACKFILL_PRIORITY_CONFIDENCE,
    BACKFILL_PRIORITY_CONFLICT,
    BACKFILL_PRIORITY_MISSING,
    CONFIDENCE_HIGH,
    CONFIDENCE_LOW,
    CONFIDENCE_MODERATE,
    CONFIDENCE_NONE,
    COVERAGE_COMPLETE,
    COVERAGE_CONFLICTING,
    COVERAGE_DISPUTED,
    COVERAGE_MISSING,
    SOURCE_TYPE_NONE,
    build_evidence_gap_backfill_plan,
    build_pd_effect_evidence_gap_report,
    group_evidence_gaps,
    summarize_pd_effect_claim_coverage,
)
from core.models import Facts, PDEffect


def _claim_trace(
    *,
    support_status="supported",
    confidence_level="moderate",
    source_type=None,
):
    evidence = []

    if source_type is not None:
        evidence.append(
            {
                "source": {
                    "source_id": "source_test_001",
                    "source_type": source_type,
                },
                "evidence_type": "clinical_reference",
                "supports_claim": support_status == "supported",
                "confidence": confidence_level,
                "notes": "test evidence",
            }
        )

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
        "evidence": evidence,
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

def test_summarize_pd_effect_claim_coverage_tracks_source_types(
    monkeypatch,
):
    monkeypatch.setattr(
        "core.evidence.completeness.build_pd_effect_traces_for_drug_effect",
        lambda drug_id, effect_id: [
            _claim_trace(source_type="drug_label"),
            _claim_trace(source_type="clinical_guideline"),
        ],
    )

    summary = summarize_pd_effect_claim_coverage(
        "test_drug",
        "nausea",
    )

    assert summary["source_types"] == [
        "clinical_guideline",
        "drug_label",
    ]


def test_summarize_pd_effect_claim_coverage_marks_missing_source_type(
    monkeypatch,
):
    monkeypatch.setattr(
        "core.evidence.completeness.build_pd_effect_traces_for_drug_effect",
        lambda drug_id, effect_id: [],
    )

    summary = summarize_pd_effect_claim_coverage(
        "test_drug",
        "nausea",
    )

    assert summary["source_types"] == [SOURCE_TYPE_NONE]


def test_group_evidence_gaps_groups_by_effect_drug_and_source_type():
    report = {
        "items": [
            {
                "drug_id": "drug_a",
                "effect_id": "nausea",
                "classification": COVERAGE_MISSING,
                "coverage_status": COVERAGE_MISSING,
                "confidence_level": None,
                "claim_count": 0,
                "source_types": [SOURCE_TYPE_NONE],
            },
            {
                "drug_id": "drug_b",
                "effect_id": "sedation",
                "classification": CONFIDENCE_LOW,
                "coverage_status": COVERAGE_COMPLETE,
                "confidence_level": "low",
                "claim_count": 1,
                "source_types": ["drug_label"],
            },
            {
                "drug_id": "drug_c",
                "effect_id": "nausea",
                "classification": CONFIDENCE_HIGH,
                "coverage_status": COVERAGE_COMPLETE,
                "confidence_level": "high",
                "claim_count": 1,
                "source_types": ["clinical_guideline"],
            },
        ],
    }

    grouped = group_evidence_gaps(report)

    assert list(grouped["by_pd_effect"]) == ["nausea", "sedation"]
    assert list(grouped["by_drug"]) == ["drug_a", "drug_b"]
    assert list(grouped["by_source_type"]) == [
        "drug_label",
        SOURCE_TYPE_NONE,
    ]

    assert grouped["by_pd_effect"]["nausea"][0]["drug_id"] == "drug_a"
    assert grouped["by_pd_effect"]["sedation"][0]["drug_id"] == "drug_b"
    assert grouped["by_drug"]["drug_a"][0]["effect_id"] == "nausea"
    assert grouped["by_source_type"]["drug_label"][0]["effect_id"] == "sedation"
    
def test_build_evidence_gap_backfill_plan_prioritizes_missing_first():
    report = {
        "items": [
            {
                "drug_id": "drug_b",
                "effect_id": "sedation",
                "classification": CONFIDENCE_LOW,
                "coverage_status": COVERAGE_COMPLETE,
                "confidence_status": CONFIDENCE_LOW,
                "confidence_level": "low",
                "claim_count": 1,
                "source_types": ["drug_label"],
            },
            {
                "drug_id": "drug_a",
                "effect_id": "nausea",
                "classification": COVERAGE_MISSING,
                "coverage_status": COVERAGE_MISSING,
                "confidence_status": CONFIDENCE_NONE,
                "confidence_level": None,
                "claim_count": 0,
                "source_types": [SOURCE_TYPE_NONE],
            },
            {
                "drug_id": "drug_c",
                "effect_id": "tachycardia",
                "classification": COVERAGE_CONFLICTING,
                "coverage_status": COVERAGE_CONFLICTING,
                "confidence_status": CONFIDENCE_MODERATE,
                "confidence_level": "moderate",
                "claim_count": 2,
                "source_types": ["case_report"],
            },
        ],
    }

    plan = build_evidence_gap_backfill_plan(report)

    assert plan["total_tasks"] == 3
    assert [task["priority"] for task in plan["tasks"]] == [
        BACKFILL_PRIORITY_MISSING,
        BACKFILL_PRIORITY_CONFLICT,
        BACKFILL_PRIORITY_CONFIDENCE,
    ]
    assert plan["tasks"][0]["drug_id"] == "drug_a"
    assert plan["tasks"][0]["effect_id"] == "nausea"
    assert plan["tasks"][0]["missing_source_types"] == ["drug_label"]
    assert "evidence" in plan["tasks"][0]["suggested_next_action"]
    assert plan["by_pd_effect"]["nausea"][0]["drug_id"] == "drug_a"
    assert plan["by_drug"]["drug_c"][0]["effect_id"] == "tachycardia"


def test_build_pd_effect_evidence_gap_report_includes_backfill_plan(
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
            ],
        },
    )

    monkeypatch.setattr(
        "core.evidence.completeness.build_pd_effect_traces_for_drug_effect",
        lambda drug_id, effect_id: [],
    )

    report = build_pd_effect_evidence_gap_report(facts)

    assert report["backfill_plan"]["total_tasks"] == 1
    assert report["backfill_plan"]["tasks"][0]["priority"] == (
        BACKFILL_PRIORITY_MISSING
    )
    assert report["backfill_plan"]["tasks"][0]["drug_id"] == "drug_a"
    assert report["backfill_plan"]["tasks"][0]["effect_id"] == "nausea"