"""Evidence confidence synthesis helpers."""

from __future__ import annotations

from typing import Any

CONFIDENCE_HIGH = "high"
CONFIDENCE_MODERATE = "moderate"
CONFIDENCE_LOW = "low"
CONFIDENCE_UNCERTAIN = "uncertain"

MIN_CONFIDENCE_SCORE = 0
MAX_CONFIDENCE_SCORE = 100

_MANUAL_CONFIDENCE_POINTS = {
    CONFIDENCE_HIGH: 25,
    CONFIDENCE_MODERATE: 15,
    CONFIDENCE_LOW: 5,
    CONFIDENCE_UNCERTAIN: 0,
}

_EVIDENCE_TYPE_POINTS = {
    "drug_label": 25,
    "clinical_guideline": 25,
    "review_article": 20,
    "primary_literature": 20,
    "internal_curated_entry": 10,
    "mechanistic_inference": 5,
    "case_report": 5,
}

_RELIABILITY_TIER_POINTS = {
    "high": 15,
    "moderate": 10,
    "low": 0,
    "curated": 10,
    "unknown": 0,
}


def clamp_confidence_score(score: int) -> int:
    """Return a confidence score constrained to 0-100."""
    return max(MIN_CONFIDENCE_SCORE, min(MAX_CONFIDENCE_SCORE, score))


def confidence_level_for_score(score: int) -> str:
    """Return a confidence level for a numeric confidence score."""
    if score >= 75:
        return CONFIDENCE_HIGH

    if score >= 50:
        return CONFIDENCE_MODERATE

    if score >= 25:
        return CONFIDENCE_UNCERTAIN

    return CONFIDENCE_LOW


def _source_reliability_tier(evidence: dict[str, Any]) -> str:
    source = evidence.get("source")

    if not isinstance(source, dict):
        return "unknown"

    tier = source.get("reliability_tier")

    if not isinstance(tier, str):
        return "unknown"

    return tier


def _score_evidence_item(evidence: dict[str, Any]) -> tuple[int, list[str]]:
    score = 0
    reasons = []

    supports_claim = evidence.get("supports_claim")
    evidence_type = evidence.get("evidence_type")
    manual_confidence = evidence.get("confidence")
    reliability_tier = _source_reliability_tier(evidence)

    if supports_claim is True:
        score += 5
        reasons.append("supporting evidence present")
    elif supports_claim is False:
        score -= 35
        reasons.append("disputing evidence present")
    else:
        reasons.append("evidence support unknown")

    if isinstance(evidence_type, str):
        points = _EVIDENCE_TYPE_POINTS.get(evidence_type, 0)
        score += points
        if points:
            reasons.append(f"{evidence_type} evidence")

    if isinstance(manual_confidence, str):
        points = _MANUAL_CONFIDENCE_POINTS.get(manual_confidence, 0)
        score += points
        reasons.append(f"manual confidence={manual_confidence}")

    reliability_points = _RELIABILITY_TIER_POINTS.get(reliability_tier, 0)
    score += reliability_points
    if reliability_points:
        reasons.append(f"source reliability={reliability_tier}")

    return score, reasons


def synthesize_claim_confidence(
    claim_trace: dict[str, Any],
) -> dict[str, Any]:
    """Return synthesized confidence metadata for a claim trace."""
    evidence_items = claim_trace.get("evidence", [])
    review = claim_trace.get("review", {})
    claim_status = claim_trace.get("claim_status")
    evidence_support_status = claim_trace.get("evidence_support_status")

    score = 0
    reasons = []

    if claim_status == "active":
        score += 5
        reasons.append("active claim")
    elif claim_status in {"deprecated", "rejected"}:
        score -= 30
        reasons.append(f"claim_status={claim_status}")

    if isinstance(review, dict):
        review_status = review.get("status")

        if review_status == "approved":
            score += 10
            reasons.append("approved review")
        elif review_status in {"submitted", "needs_changes"}:
            score -= 10
            reasons.append(f"review_status={review_status}")
        elif review_status in {"rejected", "deprecated"}:
            score -= 30
            reasons.append(f"review_status={review_status}")

    if evidence_support_status == "conflicting":
        score -= 25
        reasons.append("conflicting evidence")
    elif evidence_support_status == "disputed":
        score -= 35
        reasons.append("disputed evidence")
    elif evidence_support_status == "supported":
        score += 5
        reasons.append("claim support classified as supported")
    elif evidence_support_status == "undetermined":
        score -= 10
        reasons.append("evidence support undetermined")

    if not evidence_items:
        score -= 20
        reasons.append("no evidence items")

    for evidence in evidence_items:
        if not isinstance(evidence, dict):
            continue

        item_score, item_reasons = _score_evidence_item(evidence)
        score += item_score
        reasons.extend(item_reasons)

    score = clamp_confidence_score(score)

    return {
        "level": confidence_level_for_score(score),
        "score": score,
        "reasons": reasons,
    }