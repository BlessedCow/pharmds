import pytest

from core.evidence.governance import (
    EvidenceGovernanceError,
    claim_with_default_governance,
    has_claim_governance,
    missing_governance_fields,
    require_claim_governance,
)
from core.evidence.loader import load_pd_effect_claims


def _claim_without_governance():
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
        "evidence": [],
        "claim_status": "active",
        "review": {
            "status": "approved",
            "reviewed_by": "maintainer",
            "reviewed_at": None,
        },
    }


def test_claim_with_default_governance_adds_contributor_and_review_dates():
    claim = claim_with_default_governance(_claim_without_governance())

    assert claim["contributor"] == {
        "id": "project_maintainer",
        "role": "maintainer",
        "submitted_at": "2026-05-13",
    }
    assert claim["review"] == {
        "status": "approved",
        "reviewed_by": "maintainer",
        "reviewed_at": "2026-05-13",
    }


def test_claim_with_default_governance_does_not_mutate_input():
    original = _claim_without_governance()

    claim_with_default_governance(original)

    assert "contributor" not in original
    assert original["review"]["reviewed_at"] is None


def test_missing_governance_fields_reports_missing_nested_fields():
    missing = missing_governance_fields(_claim_without_governance())

    assert missing == [
        "contributor.id",
        "contributor.role",
        "contributor.submitted_at",
        "review.reviewed_at",
    ]


def test_require_claim_governance_raises_for_incomplete_claim():
    with pytest.raises(EvidenceGovernanceError) as exc_info:
        require_claim_governance(_claim_without_governance())

    assert "claim_fluconazole_pd_effect_QT_prolongation_001" in str(
        exc_info.value
    )
    assert "contributor.id" in str(exc_info.value)


def test_has_claim_governance_returns_true_for_backfilled_claim():
    claim = claim_with_default_governance(_claim_without_governance())

    assert has_claim_governance(claim) is True


def test_all_loaded_pd_effect_claims_have_governance_metadata():
    claims = load_pd_effect_claims()

    assert claims
    assert all(has_claim_governance(claim) for claim in claims)