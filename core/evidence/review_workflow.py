"""Review workflow helpers for evidence claims."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

REVIEW_STATUS_DRAFT = "draft"
REVIEW_STATUS_SUBMITTED = "submitted"
REVIEW_STATUS_NEEDS_CHANGES = "needs_changes"
REVIEW_STATUS_APPROVED = "approved"
REVIEW_STATUS_DEPRECATED = "deprecated"
REVIEW_STATUS_REJECTED = "rejected"

CLAIM_STATUS_DRAFT = "draft"
CLAIM_STATUS_ACTIVE = "active"
CLAIM_STATUS_DEPRECATED = "deprecated"
CLAIM_STATUS_REJECTED = "rejected"

VALID_REVIEW_STATUSES = {
    REVIEW_STATUS_DRAFT,
    REVIEW_STATUS_SUBMITTED,
    REVIEW_STATUS_NEEDS_CHANGES,
    REVIEW_STATUS_APPROVED,
    REVIEW_STATUS_DEPRECATED,
    REVIEW_STATUS_REJECTED,
}


class EvidenceReviewWorkflowError(ValueError):
    """Raised when an evidence claim review workflow action is invalid."""


def _copy_claim(claim: dict[str, Any]) -> dict[str, Any]:
    """Return a deep copy of an evidence claim."""
    return deepcopy(claim)


def _ensure_review(claim: dict[str, Any]) -> dict[str, Any]:
    """Return the claim review dictionary, creating it if needed."""
    return claim.setdefault("review", {})


def _set_review_status(
    claim: dict[str, Any],
    status: str,
    *,
    reviewed_by: str | None = None,
    reviewed_at: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    """Return a claim copy with updated review metadata."""
    if status not in VALID_REVIEW_STATUSES:
        raise EvidenceReviewWorkflowError(f"Invalid review status: {status}")

    updated = _copy_claim(claim)
    review = _ensure_review(updated)

    review["status"] = status

    if reviewed_by is not None:
        review["reviewed_by"] = reviewed_by

    if reviewed_at is not None:
        review["reviewed_at"] = reviewed_at

    if reason is not None:
        review["reason"] = reason

    return updated


def submit_claim(claim: dict[str, Any]) -> dict[str, Any]:
    """Return a claim marked as submitted for review."""
    updated = _set_review_status(claim, REVIEW_STATUS_SUBMITTED)
    updated["claim_status"] = CLAIM_STATUS_DRAFT

    return updated


def approve_claim(
    claim: dict[str, Any],
    *,
    reviewed_by: str,
    reviewed_at: str,
) -> dict[str, Any]:
    """Return a claim marked as approved and active."""
    updated = _set_review_status(
        claim,
        REVIEW_STATUS_APPROVED,
        reviewed_by=reviewed_by,
        reviewed_at=reviewed_at,
    )
    updated["claim_status"] = CLAIM_STATUS_ACTIVE

    return updated


def request_changes(
    claim: dict[str, Any],
    *,
    reviewed_by: str,
    reviewed_at: str,
    reason: str,
) -> dict[str, Any]:
    """Return a claim marked as needing changes."""
    updated = _set_review_status(
        claim,
        REVIEW_STATUS_NEEDS_CHANGES,
        reviewed_by=reviewed_by,
        reviewed_at=reviewed_at,
        reason=reason,
    )
    updated["claim_status"] = CLAIM_STATUS_DRAFT

    return updated


def reject_claim(
    claim: dict[str, Any],
    *,
    reviewed_by: str,
    reviewed_at: str,
    reason: str,
) -> dict[str, Any]:
    """Return a claim marked as rejected."""
    updated = _set_review_status(
        claim,
        REVIEW_STATUS_REJECTED,
        reviewed_by=reviewed_by,
        reviewed_at=reviewed_at,
        reason=reason,
    )
    updated["claim_status"] = CLAIM_STATUS_REJECTED

    return updated


def deprecate_claim(
    claim: dict[str, Any],
    *,
    reviewed_by: str,
    reviewed_at: str,
    reason: str,
) -> dict[str, Any]:
    """Return a claim marked as deprecated."""
    updated = _set_review_status(
        claim,
        REVIEW_STATUS_DEPRECATED,
        reviewed_by=reviewed_by,
        reviewed_at=reviewed_at,
        reason=reason,
    )
    updated["claim_status"] = CLAIM_STATUS_DEPRECATED

    return updated


def is_approved_active_claim(claim: dict[str, Any]) -> bool:
    """Return whether a claim is approved and active."""
    return (
        claim.get("claim_status") == CLAIM_STATUS_ACTIVE
        and claim.get("review", {}).get("status") == REVIEW_STATUS_APPROVED
    )