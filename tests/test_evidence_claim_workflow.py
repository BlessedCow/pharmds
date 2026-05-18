import pytest

from core.evidence.claim_workflow import (
    EvidenceClaimWorkflowError,
    approve_draft_claim,
    contributor_submission_to_approved_claim,
    mark_draft_claim_under_review,
    require_valid_evidence_claim,
    validate_evidence_claim,
)
from core.evidence.contributor_claims import (
    contributor_submission_to_validated_draft_claim,
)


def _valid_submission():
    return {
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
                "source_id": "source_internal_curated_pd_effects_v1",
                "evidence_type": "internal_curated_entry",
                "supports_claim": True,
                "confidence": "moderate",
                "notes": "Contributor-submitted evidence.",
            }
        ],
        "contributor": {
            "id": "test_contributor",
            "role": "contributor",
            "submitted_at": "2026-05-18",
        },
        "review": {
            "status": "submitted",
        },
    }


def test_validate_evidence_claim_accepts_approved_claim():
    draft = contributor_submission_to_validated_draft_claim(
        _valid_submission(),
    )
    approved = approve_draft_claim(
        draft,
        reviewed_by="maintainer",
        reviewed_at="2026-05-18",
    )

    assert validate_evidence_claim(approved) == []


def test_approve_draft_claim_promotes_to_active_approved_claim():
    draft = contributor_submission_to_validated_draft_claim(
        _valid_submission(),
    )

    approved = approve_draft_claim(
        draft,
        reviewed_by="maintainer",
        reviewed_at="2026-05-18",
    )

    assert approved["claim_id"] == (
        "claim_fluconazole_pd_effect_QT_prolongation_001"
    )
    assert approved["claim_status"] == "active"
    assert approved["review"] == {
        "status": "approved",
        "reviewed_by": "maintainer",
        "reviewed_at": "2026-05-18",
    }
    assert approved["contributor"] == {
        "id": "test_contributor",
        "role": "contributor",
        "submitted_at": "2026-05-18",
    }


def test_approve_draft_claim_does_not_mutate_input():
    draft = contributor_submission_to_validated_draft_claim(
        _valid_submission(),
    )

    approve_draft_claim(
        draft,
        reviewed_by="maintainer",
        reviewed_at="2026-05-18",
    )

    assert draft["claim_status"] == "draft"
    assert draft["review"]["status"] == "submitted"


def test_approve_draft_claim_requires_reviewer_metadata():
    draft = contributor_submission_to_validated_draft_claim(
        _valid_submission(),
    )

    with pytest.raises(EvidenceClaimWorkflowError):
        approve_draft_claim(
            draft,
            reviewed_by="",
            reviewed_at="2026-05-18",
        )

    with pytest.raises(EvidenceClaimWorkflowError):
        approve_draft_claim(
            draft,
            reviewed_by="maintainer",
            reviewed_at="",
        )


def test_contributor_submission_to_approved_claim_validates_and_promotes():
    approved = contributor_submission_to_approved_claim(
        _valid_submission(),
        reviewed_by="maintainer",
        reviewed_at="2026-05-18",
    )

    assert approved["claim_status"] == "active"
    assert approved["review"]["status"] == "approved"
    assert validate_evidence_claim(approved) == []


def test_require_valid_evidence_claim_raises_for_invalid_claim():
    with pytest.raises(EvidenceClaimWorkflowError):
        require_valid_evidence_claim(
            {
                "claim_id": "not_valid",
            }
        )


def test_mark_draft_claim_under_review_marks_claim_without_mutating_input():
    draft = contributor_submission_to_validated_draft_claim(
        _valid_submission(),
    )

    under_review = mark_draft_claim_under_review(draft)

    assert under_review["claim_status"] == "under_review"
    assert under_review["review"]["status"] == "submitted"
    assert draft["claim_status"] == "draft"