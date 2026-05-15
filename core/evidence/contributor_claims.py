"""Helpers for normalizing contributor evidence claim submissions."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

CLAIM_TYPE_PD_EFFECT = "pd_effect"
PREDICATE_HAS_PD_EFFECT = "has_pd_effect"
DEFAULT_CONTRIBUTOR_REVIEW_STATUS = "submitted"
DEFAULT_CONTRIBUTOR_CLAIM_STATUS = "draft"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTRIBUTOR_PD_EFFECT_SCHEMA_PATH = (
    PROJECT_ROOT
    / "data"
    / "evidence"
    / "schemas"
    / "contributor_pd_effect_claim.schema.json"
)


class ContributorClaimValidationError(ValueError):
    """Raised when a contributor claim submission fails validation."""


def build_pd_effect_claim_id(drug_id: str, effect_id: str) -> str:
    """Return the canonical claim ID for a drug PD effect claim."""
    return f"claim_{drug_id}_pd_effect_{effect_id}_001"


def load_contributor_pd_effect_claim_schema() -> dict[str, Any]:
    """Load the contributor PD effect claim JSON schema."""
    return json.loads(
        CONTRIBUTOR_PD_EFFECT_SCHEMA_PATH.read_text(encoding="utf-8"),
    )


def validate_contributor_pd_effect_submission(
    submission: dict[str, Any],
) -> list[str]:
    """Return validation error messages for a contributor PD effect submission."""
    schema = load_contributor_pd_effect_claim_schema()
    validator = Draft202012Validator(schema)

    errors = sorted(
        validator.iter_errors(submission),
        key=lambda error: list(error.path),
    )

    return [
        f"{list(error.path)}: {error.message}"
        for error in errors
    ]


def require_valid_contributor_pd_effect_submission(
    submission: dict[str, Any],
) -> None:
    """Raise if a contributor PD effect submission is invalid."""
    errors = validate_contributor_pd_effect_submission(submission)

    if errors:
        raise ContributorClaimValidationError("; ".join(errors))


def contributor_submission_to_draft_claim(
    submission: dict[str, Any],
) -> dict[str, Any]:
    """Convert a contributor PD effect submission into a normalized draft claim."""
    normalized = deepcopy(submission)

    drug_id = normalized["subject"]["id"]
    effect_id = normalized["object"]["effect_id"]

    normalized["claim_id"] = build_pd_effect_claim_id(drug_id, effect_id)
    normalized["claim_status"] = DEFAULT_CONTRIBUTOR_CLAIM_STATUS

    review = normalized.setdefault("review", {})
    review.setdefault("status", DEFAULT_CONTRIBUTOR_REVIEW_STATUS)
    review.setdefault("reviewed_by", None)
    review.setdefault("reviewed_at", None)

    return normalized


def contributor_submission_to_validated_draft_claim(
    submission: dict[str, Any],
) -> dict[str, Any]:
    """Validate a contributor submission and convert it into a draft claim."""
    require_valid_contributor_pd_effect_submission(submission)

    return contributor_submission_to_draft_claim(submission)


def is_contributor_pd_effect_submission(
    submission: dict[str, Any],
) -> bool:
    """Return whether a submission has the expected PD effect claim shape."""
    return (
        submission.get("claim_type") == CLAIM_TYPE_PD_EFFECT
        and submission.get("predicate") == PREDICATE_HAS_PD_EFFECT
        and submission.get("subject", {}).get("entity_type") == "drug"
        and "id" in submission.get("subject", {})
        and "effect_id" in submission.get("object", {})
    )