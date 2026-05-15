import pytest

from core.evidence.review_workflow import (
    CLAIM_STATUS_ACTIVE,
    CLAIM_STATUS_DEPRECATED,
    CLAIM_STATUS_DRAFT,
    CLAIM_STATUS_REJECTED,
    EvidenceReviewWorkflowError,
    approve_claim,
    deprecate_claim,
    is_approved_active_claim,
    reject_claim,
    request_changes,
    submit_claim,
)


def _draft_claim():
    return {
        "claim_id": "claim_fluconazole_pd_effect_QT_prolongation_001",
        "claim_type": "pd_effect",
        "subject": {
            "entity_type": "drug",
            "id": "fluconazole",
        },
        "predicate": "has_pd_effect",
        "object": {
            "effect_id": "QT_prolongation",
        },
        "evidence": [
            {
                "source_id": "source_dailymed_fluconazole_label",
                "evidence_type": "drug_label",
                "supports_claim": True,
                "confidence": "moderate",
                "notes": "Contributor-submitted label evidence.",
            }
        ],
        "review": {
            "status": "draft",
        },
        "claim_status": "draft",
    }


def test_submit_claim_marks_claim_as_submitted_draft():
    submitted = submit_claim(_draft_claim())

    assert submitted["claim_status"] == CLAIM_STATUS_DRAFT
    assert submitted["review"]["status"] == "submitted"


def test_approve_claim_marks_claim_as_approved_active():
    approved = approve_claim(
        _draft_claim(),
        reviewed_by="maintainer",
        reviewed_at="2026-05-15",
    )

    assert approved["claim_status"] == CLAIM_STATUS_ACTIVE
    assert approved["review"] == {
        "status": "approved",
        "reviewed_by": "maintainer",
        "reviewed_at": "2026-05-15",
    }


def test_request_changes_marks_claim_as_needing_changes():
    claim = request_changes(
        _draft_claim(),
        reviewed_by="maintainer",
        reviewed_at="2026-05-15",
        reason="Needs a more specific source citation.",
    )

    assert claim["claim_status"] == CLAIM_STATUS_DRAFT
    assert claim["review"] == {
        "status": "needs_changes",
        "reviewed_by": "maintainer",
        "reviewed_at": "2026-05-15",
        "reason": "Needs a more specific source citation.",
    }


def test_reject_claim_marks_claim_as_rejected():
    claim = reject_claim(
        _draft_claim(),
        reviewed_by="maintainer",
        reviewed_at="2026-05-15",
        reason="Source does not support the claim.",
    )

    assert claim["claim_status"] == CLAIM_STATUS_REJECTED
    assert claim["review"] == {
        "status": "rejected",
        "reviewed_by": "maintainer",
        "reviewed_at": "2026-05-15",
        "reason": "Source does not support the claim.",
    }


def test_deprecate_claim_marks_claim_as_deprecated():
    claim = deprecate_claim(
        _draft_claim(),
        reviewed_by="maintainer",
        reviewed_at="2026-05-15",
        reason="Replaced by a newer evidence claim.",
    )

    assert claim["claim_status"] == CLAIM_STATUS_DEPRECATED
    assert claim["review"] == {
        "status": "deprecated",
        "reviewed_by": "maintainer",
        "reviewed_at": "2026-05-15",
        "reason": "Replaced by a newer evidence claim.",
    }


def test_workflow_helpers_do_not_mutate_input_claim():
    claim = _draft_claim()

    approve_claim(
        claim,
        reviewed_by="maintainer",
        reviewed_at="2026-05-15",
    )

    assert claim["claim_status"] == "draft"
    assert claim["review"] == {
        "status": "draft",
    }


def test_is_approved_active_claim_returns_true_for_approved_active_claim():
    claim = approve_claim(
        _draft_claim(),
        reviewed_by="maintainer",
        reviewed_at="2026-05-15",
    )

    assert is_approved_active_claim(claim) is True


def test_is_approved_active_claim_returns_false_for_submitted_draft_claim():
    claim = submit_claim(_draft_claim())

    assert is_approved_active_claim(claim) is False


def test_invalid_review_status_raises_error():
    from core.evidence.review_workflow import _set_review_status

    with pytest.raises(EvidenceReviewWorkflowError):
        _set_review_status(_draft_claim(), "not_a_real_status")