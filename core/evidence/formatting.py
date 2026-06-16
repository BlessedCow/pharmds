"""Formatting helpers for evidence and source traces."""

from __future__ import annotations

from typing import Any


def display_value(value: object, fallback: str = "unknown") -> str:
    """Return a readable display value."""
    if value is None:
        return fallback

    if value == "":
        return fallback

    return str(value)


def format_source_trace(source: dict[str, Any]) -> str:
    """Return a display-ready source trace summary."""
    if not source.get("found", False):
        source_id = display_value(source.get("source_id"), "unknown_source")
        return f"{source_id} (source not found)"

    title = display_value(source.get("title"), "Unknown source")
    publisher = display_value(source.get("publisher"))
    reliability_tier = display_value(source.get("reliability_tier"))
    accessed_at = source.get("accessed_at")

    if accessed_at:
        return (
            f"{title} ({publisher}, {reliability_tier}; "
            f"accessed {accessed_at})"
        )

    return f"{title} ({publisher}, {reliability_tier})"


def format_evidence_item_trace(evidence: dict[str, Any]) -> str:
    """Return a display-ready evidence item summary."""
    evidence_type = display_value(evidence.get("evidence_type"))
    confidence = display_value(evidence.get("confidence"))
    supports_claim = evidence.get("supports_claim")
    support_label = "supports_claim=unknown"

    if supports_claim is True:
        support_label = "supports_claim=true"
    elif supports_claim is False:
        support_label = "supports_claim=false"

    source = evidence.get("source", {})

    if not isinstance(source, dict):
        source = {}

    source_summary = format_source_trace(source)

    return (
        f"{source_summary}; evidence_type={evidence_type}; "
        f"{support_label}; confidence={confidence}"
    )


def format_claim_trace(claim: dict[str, Any]) -> str:
    """Return a display-ready claim trace summary."""
    drug_id = display_value(claim.get("drug_id"), "unknown_drug")
    effect_id = display_value(claim.get("effect_id"), "unknown_effect")
    claim_type = display_value(claim.get("claim_type"), "unknown_claim_type")
    claim_status = display_value(claim.get("claim_status"))

    review = claim.get("review", {})

    if not isinstance(review, dict):
        review = {}

    review_status = display_value(review.get("status"))

    evidence_support_status = display_value(
        claim.get("evidence_support_status"),
        "unknown",
    )
    evidence_confidence = format_evidence_confidence(
        claim.get("evidence_confidence"),
    )
    evidence_items = claim.get("evidence", [])

    if not evidence_items:
        return (
            f"{drug_id} -> {effect_id}: {claim_type}; "
            f"claim_status={claim_status}; review_status={review_status}; "
            f"evidence_support_status={evidence_support_status}; "
            f"evidence_confidence={evidence_confidence}; "
            "evidence=none"
        )
    evidence_summary = format_evidence_item_trace(evidence_items[0])

    return (
        f"{drug_id} -> {effect_id}: {claim_type}; "
        f"claim_status={claim_status}; review_status={review_status}; "
        f"evidence_support_status={evidence_support_status}; "
        f"evidence_confidence={evidence_confidence}; "
        f"evidence={evidence_summary}"
    )

def format_evidence_confidence(confidence: dict[str, Any] | None) -> str:
    """Return a compact synthesized confidence summary."""
    if not isinstance(confidence, dict):
        return "unknown"

    level = display_value(confidence.get("level"))
    score = display_value(confidence.get("score"))

    return f"{level}({score})"


def format_evidence_trace(trace: dict[str, Any]) -> list[str]:
    """Return display-ready lines for an evidence trace."""
    effect_id = display_value(trace.get("effect_id"), "unknown_effect")
    overall_status = display_value(
        trace.get("overall_evidence_status"),
        "unknown",
    )
    drug_traces = trace.get("drugs", [])

    lines = [f"Evidence status for {effect_id}: {overall_status}"]

    for drug_trace in drug_traces:
        if not isinstance(drug_trace, dict):
            continue

        drug_id = display_value(drug_trace.get("drug_id"), "unknown_drug")
        evidence_status = display_value(
            drug_trace.get("evidence_status"),
            "unknown",
        )
        claims = drug_trace.get("claims", [])

        if not claims:
            lines.append(
                f"{drug_id} -> {effect_id}: evidence_status={evidence_status}; "
                "claims=none"
            )
            continue

        claim_summaries = [
            format_claim_trace(claim)
            for claim in claims
            if isinstance(claim, dict)
        ]

        if not claim_summaries:
            lines.append(
                f"{drug_id} -> {effect_id}: evidence_status={evidence_status}; "
                "claims=none"
            )
            continue

        for claim_summary in claim_summaries:
            lines.append(
                f"{drug_id} evidence_status={evidence_status}; "
                f"{claim_summary}"
            )

    return lines