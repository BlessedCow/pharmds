"""Conflict classification helpers for evidence claims."""

from __future__ import annotations

from typing import Any

EVIDENCE_SUPPORT_SUPPORTED = "supported"
EVIDENCE_SUPPORT_DISPUTED = "disputed"
EVIDENCE_SUPPORT_CONFLICTING = "conflicting"
EVIDENCE_SUPPORT_UNDETERMINED = "undetermined"


def count_evidence_support(evidence_items: list[dict[str, Any]]) -> dict[str, int]:
    """Count supporting and disputing evidence items."""
    supporting = 0
    disputing = 0

    for evidence in evidence_items:
        supports_claim = evidence.get("supports_claim")

        if supports_claim is True:
            supporting += 1
        elif supports_claim is False:
            disputing += 1

    return {
        "supporting": supporting,
        "disputing": disputing,
    }


def classify_evidence_support(
    evidence_items: list[dict[str, Any]],
) -> str:
    """Classify whether evidence supports, disputes, or conflicts."""
    counts = count_evidence_support(evidence_items)
    supporting = counts["supporting"]
    disputing = counts["disputing"]

    if supporting and disputing:
        return EVIDENCE_SUPPORT_CONFLICTING

    if supporting:
        return EVIDENCE_SUPPORT_SUPPORTED

    if disputing:
        return EVIDENCE_SUPPORT_DISPUTED

    return EVIDENCE_SUPPORT_UNDETERMINED


def claim_has_supporting_evidence(claim: dict[str, Any]) -> bool:
    """Return whether a claim has at least one supporting evidence item."""
    return any(
        evidence.get("supports_claim") is True
        for evidence in claim.get("evidence", [])
        if isinstance(evidence, dict)
    )


def claim_has_disputing_evidence(claim: dict[str, Any]) -> bool:
    """Return whether a claim has at least one disputing evidence item."""
    return any(
        evidence.get("supports_claim") is False
        for evidence in claim.get("evidence", [])
        if isinstance(evidence, dict)
    )