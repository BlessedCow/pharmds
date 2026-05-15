import pytest

from core.evidence.contributor_claims import (
    ContributorClaimValidationError,
    build_pd_effect_claim_id,
    contributor_submission_to_draft_claim,
    contributor_submission_to_validated_draft_claim,
    is_contributor_pd_effect_submission,
    load_contributor_pd_effect_claim_schema,
    require_valid_contributor_pd_effect_submission,
    validate_contributor_pd_effect_submission,
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
                "source_id": "source_dailymed_fluconazole_label",
                "evidence_type": "drug_label",
                "supports_claim": True,
                "confidence": "moderate",
                "notes": "Contributor-submitted label evidence.",
            }
        ],
        "contributor": {
            "id": "project_maintainer",
            "role": "maintainer",
            "submitted_at": "2026-05-13",
        },
        "review": {
            "status": "submitted",
        },
    }


def test_build_pd_effect_claim_id_returns_canonical_id():
    assert build_pd_effect_claim_id(
        "fluconazole",
        "QT_prolongation",
    ) == "claim_fluconazole_pd_effect_QT_prolongation_001"


def test_contributor_submission_to_draft_claim_adds_claim_metadata():
    draft = contributor_submission_to_draft_claim(_valid_submission())

    assert draft["claim_id"] == (
        "claim_fluconazole_pd_effect_QT_prolongation_001"
    )
    assert draft["claim_status"] == "draft"
    assert draft["review"] == {
        "status": "submitted",
        "reviewed_by": None,
        "reviewed_at": None,
    }


def test_contributor_submission_to_draft_claim_preserves_submission_content():
    submission = _valid_submission()
    draft = contributor_submission_to_draft_claim(submission)

    assert draft["claim_type"] == "pd_effect"
    assert draft["subject"] == {
        "entity_type": "drug",
        "id": "fluconazole",
    }
    assert draft["predicate"] == "has_pd_effect"
    assert draft["object"] == {
        "effect_id": "QT_prolongation",
    }
    assert draft["evidence"] == submission["evidence"]


def test_contributor_submission_to_draft_claim_does_not_mutate_input():
    submission = _valid_submission()

    contributor_submission_to_draft_claim(submission)

    assert "claim_id" not in submission
    assert "claim_status" not in submission
    assert submission["review"] == {
        "status": "submitted",
    }


def test_is_contributor_pd_effect_submission_returns_true_for_valid_shape():
    assert is_contributor_pd_effect_submission(_valid_submission()) is True


def test_is_contributor_pd_effect_submission_returns_false_for_wrong_claim_type():
    submission = _valid_submission()
    submission["claim_type"] = "enzyme_role"

    assert is_contributor_pd_effect_submission(submission) is False


def test_is_contributor_pd_effect_submission_returns_false_for_missing_effect():
    submission = _valid_submission()
    submission["object"] = {}

    assert is_contributor_pd_effect_submission(submission) is False
    
def test_load_contributor_pd_effect_claim_schema_returns_schema():
    schema = load_contributor_pd_effect_claim_schema()

    assert schema["title"] == "Contributor PD Effect Claim"
    assert schema["type"] == "object"


def test_validate_contributor_pd_effect_submission_accepts_valid_submission():
    errors = validate_contributor_pd_effect_submission(_valid_submission())

    assert errors == []

def test_validate_contributor_pd_effect_submission_rejects_invalid_submission():
    submission = _valid_submission()
    submission["review"]["status"] = "approved"

    errors = validate_contributor_pd_effect_submission(submission)

    assert errors
    assert "['review', 'status']" in errors[0]


def test_require_valid_contributor_pd_effect_submission_accepts_valid_submission():
    require_valid_contributor_pd_effect_submission(_valid_submission())


def test_require_valid_contributor_pd_effect_submission_raises_for_invalid_submission():
    submission = _valid_submission()
    submission["evidence"] = []

    with pytest.raises(ContributorClaimValidationError) as exc_info:
        require_valid_contributor_pd_effect_submission(submission)

    assert "['evidence']" in str(exc_info.value)


def test_contributor_submission_to_validated_draft_claim_returns_draft_claim():
    draft = contributor_submission_to_validated_draft_claim(_valid_submission())

    assert draft["claim_id"] == (
        "claim_fluconazole_pd_effect_QT_prolongation_001"
    )
    assert draft["claim_status"] == "draft"
    assert draft["review"]["status"] == "submitted"


def test_contributor_submission_to_validated_draft_claim_rejects_invalid_submission():
    submission = _valid_submission()
    submission["claim_status"] = "active"

    with pytest.raises(ContributorClaimValidationError):
        contributor_submission_to_validated_draft_claim(submission)
        
    