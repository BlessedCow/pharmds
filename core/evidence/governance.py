"""Governance metadata helpers for evidence claims."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

DEFAULT_CONTRIBUTOR_ID = "project_maintainer"
DEFAULT_CONTRIBUTOR_ROLE = "maintainer"
DEFAULT_SUBMITTED_AT = "2026-05-13"
DEFAULT_REVIEWED_BY = "maintainer"
DEFAULT_REVIEWED_AT = "2026-05-13"

REQUIRED_CONTRIBUTOR_FIELDS = {
    "id",
    "role",
    "submitted_at",
}
REQUIRED_REVIEW_FIELDS = {
    "status",
    "reviewed_by",
    "reviewed_at",
}


class EvidenceGovernanceError(ValueError):
    """Raised when evidence governance metadata is missing or invalid."""


def default_contributor_metadata() -> dict[str, str]:
    """Return default contributor metadata for migrated curated claims."""
    return {
        "id": DEFAULT_CONTRIBUTOR_ID,
        "role": DEFAULT_CONTRIBUTOR_ROLE,
        "submitted_at": DEFAULT_SUBMITTED_AT,
    }


def default_approved_review_metadata() -> dict[str, str]:
    """Return default approved review metadata for migrated curated claims."""
    return {
        "status": "approved",
        "reviewed_by": DEFAULT_REVIEWED_BY,
        "reviewed_at": DEFAULT_REVIEWED_AT,
    }


def claim_with_default_governance(
    claim: dict[str, Any],
) -> dict[str, Any]:
    """Return a claim copy with default contributor and review metadata."""
    updated = deepcopy(claim)

    contributor = updated.setdefault("contributor", {})
    for key, value in default_contributor_metadata().items():
        if contributor.get(key) in (None, ""):
            contributor[key] = value

    review = updated.setdefault("review", {})
    for key, value in default_approved_review_metadata().items():
        if review.get(key) in (None, ""):
            review[key] = value

    return updated


def missing_governance_fields(claim: dict[str, Any]) -> list[str]:
    """Return missing governance fields for an evidence claim."""
    missing = []
    contributor = claim.get("contributor", {})
    review = claim.get("review", {})

    if not isinstance(contributor, dict):
        missing.append("contributor")
    else:
        for field in sorted(REQUIRED_CONTRIBUTOR_FIELDS):
            if contributor.get(field) in (None, ""):
                missing.append(f"contributor.{field}")

    if not isinstance(review, dict):
        missing.append("review")
    else:
        for field in sorted(REQUIRED_REVIEW_FIELDS):
            if review.get(field) in (None, ""):
                missing.append(f"review.{field}")

    return missing


def require_claim_governance(claim: dict[str, Any]) -> None:
    """Raise if a claim lacks required governance metadata."""
    missing = missing_governance_fields(claim)

    if missing:
        claim_id = claim.get("claim_id", "unknown_claim")
        raise EvidenceGovernanceError(
            f"Claim {claim_id} is missing governance fields: "
            f"{', '.join(missing)}"
        )


def has_claim_governance(claim: dict[str, Any]) -> bool:
    """Return whether a claim has required governance metadata."""
    return missing_governance_fields(claim) == []