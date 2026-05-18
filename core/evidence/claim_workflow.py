"""Evidence claim authoring and review workflow helpers."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from core.evidence.contributor_claims import (
    contributor_submission_to_validated_draft_claim,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_CLAIM_SCHEMA_PATH = (
    PROJECT_ROOT / "schemas" / "evidence" / "evidence_claim.schema.json"
)

APPROVED_REVIEW_STATUS = "approved"
ACTIVE_CLAIM_STATUS = "active"
UNDER_REVIEW_CLAIM_STATUS = "under_review"


class EvidenceClaimWorkflowError(ValueError):
    """Raised when evidence claim workflow validation fails."""


def load_evidence_claim_schema() -> dict[str, Any]:
    """Load the stored evidence claim JSON schema."""
    return json.loads(
        EVIDENCE_CLAIM_SCHEMA_PATH.read_text(encoding="utf-8"),
    )


def validate_evidence_claim(
    claim: dict[str, Any],
) -> list[str]:
    """Return validation error messages for a stored evidence claim."""
    schema = load_evidence_claim_schema()
    validator = Draft202012Validator(schema)
    errors = sorted(
        validator.iter_errors(claim),
        key=lambda error: list(error.path),
    )

    return [
        f"{list(error.path)}: {error.message}"
        for error in errors
    ]


def require_valid_evidence_claim(
    claim: dict[str, Any],
) -> None:
    """Raise if a stored evidence claim is invalid."""
    errors = validate_evidence_claim(claim)

    if errors:
        raise EvidenceClaimWorkflowError("; ".join(errors))


def mark_draft_claim_under_review(
    draft_claim: dict[str, Any],
) -> dict[str, Any]:
    """Return a draft claim marked as under review."""
    updated = deepcopy(draft_claim)
    updated["claim_status"] = UNDER_REVIEW_CLAIM_STATUS
    review = updated.setdefault("review", {})
    review["status"] = "submitted"

    return updated


def approve_draft_claim(
    draft_claim: dict[str, Any],
    *,
    reviewed_by: str,
    reviewed_at: str,
) -> dict[str, Any]:
    """Return a draft evidence claim promoted to approved active status."""
    if not reviewed_by:
        raise EvidenceClaimWorkflowError("reviewed_by is required")

    if not reviewed_at:
        raise EvidenceClaimWorkflowError("reviewed_at is required")

    approved = deepcopy(draft_claim)
    approved["claim_status"] = ACTIVE_CLAIM_STATUS
    review = approved.setdefault("review", {})
    review["status"] = APPROVED_REVIEW_STATUS
    review["reviewed_by"] = reviewed_by
    review["reviewed_at"] = reviewed_at

    require_valid_evidence_claim(approved)

    return approved


def contributor_submission_to_approved_claim(
    submission: dict[str, Any],
    *,
    reviewed_by: str,
    reviewed_at: str,
) -> dict[str, Any]:
    """Validate a contributor submission and return an approved claim."""
    draft_claim = contributor_submission_to_validated_draft_claim(submission)

    return approve_draft_claim(
        draft_claim,
        reviewed_by=reviewed_by,
        reviewed_at=reviewed_at,
    )