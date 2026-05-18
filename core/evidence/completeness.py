"""Evidence completeness reporting helpers."""

from __future__ import annotations

from collections import Counter
from typing import Any

from core.evidence.traces import build_pd_effect_traces_for_drug_effect
from core.models import Facts

COVERAGE_COMPLETE = "complete"
COVERAGE_MISSING = "missing"
COVERAGE_CONFLICTING = "conflicting"
COVERAGE_DISPUTED = "disputed"
COVERAGE_UNDETERMINED = "undetermined"

CONFIDENCE_HIGH = "high_confidence"
CONFIDENCE_MODERATE = "moderate_confidence"
CONFIDENCE_LOW = "low_confidence"
CONFIDENCE_UNCERTAIN = "uncertain_confidence"
CONFIDENCE_NONE = "no_confidence"

_CONFIDENCE_RANK = {
    "low": 1,
    "uncertain": 2,
    "moderate": 3,
    "high": 4,
}

_CONFIDENCE_STATUS_BY_LEVEL = {
    "high": CONFIDENCE_HIGH,
    "moderate": CONFIDENCE_MODERATE,
    "low": CONFIDENCE_LOW,
    "uncertain": CONFIDENCE_UNCERTAIN,
}


def _effect_id_from_pd_effect(effect: Any) -> str | None:
    effect_id = getattr(effect, "effect_id", None)

    if not isinstance(effect_id, str):
        return None

    if not effect_id:
        return None

    return effect_id


def _confidence_level_from_claim_trace(
    claim_trace: dict[str, Any],
) -> str | None:
    confidence = claim_trace.get("evidence_confidence")

    if not isinstance(confidence, dict):
        return None

    level = confidence.get("level")

    if not isinstance(level, str):
        return None

    return level


def _highest_confidence_level(
    claim_traces: list[dict[str, Any]],
) -> str | None:
    levels = [
        level
        for claim_trace in claim_traces
        if (level := _confidence_level_from_claim_trace(claim_trace))
    ]

    if not levels:
        return None

    return max(levels, key=lambda level: _CONFIDENCE_RANK.get(level, 0))


def _confidence_status_for_level(level: str | None) -> str:
    if level is None:
        return CONFIDENCE_NONE

    return _CONFIDENCE_STATUS_BY_LEVEL.get(level, CONFIDENCE_NONE)


def _coverage_status_for_claim_traces(
    claim_traces: list[dict[str, Any]],
) -> str:
    if not claim_traces:
        return COVERAGE_MISSING

    support_statuses = {
        claim_trace.get("evidence_support_status")
        for claim_trace in claim_traces
    }

    if "conflicting" in support_statuses:
        return COVERAGE_CONFLICTING

    if "supported" in support_statuses and "disputed" in support_statuses:
        return COVERAGE_CONFLICTING

    if "supported" in support_statuses:
        return COVERAGE_COMPLETE

    if "disputed" in support_statuses:
        return COVERAGE_DISPUTED

    return COVERAGE_UNDETERMINED


def _classification_for_summary(
    coverage_status: str,
    confidence_status: str,
) -> str:
    if coverage_status != COVERAGE_COMPLETE:
        return coverage_status

    return confidence_status


def summarize_pd_effect_claim_coverage(
    drug_id: str,
    effect_id: str,
) -> dict[str, Any]:
    """Return evidence coverage summary for one drug/effect pair."""
    claim_traces = build_pd_effect_traces_for_drug_effect(
        drug_id,
        effect_id,
    )
    coverage_status = _coverage_status_for_claim_traces(claim_traces)
    confidence_level = _highest_confidence_level(claim_traces)
    confidence_status = _confidence_status_for_level(confidence_level)

    return {
        "drug_id": drug_id,
        "effect_id": effect_id,
        "coverage_status": coverage_status,
        "confidence_level": confidence_level,
        "confidence_status": confidence_status,
        "classification": _classification_for_summary(
            coverage_status,
            confidence_status,
        ),
        "claim_count": len(claim_traces),
        "claims": claim_traces,
    }


def build_pd_effect_evidence_gap_report(
    facts: Facts,
) -> dict[str, Any]:
    """Return a maintainer-facing PD effect evidence coverage report."""
    items = []

    for drug_id in sorted(facts.pd_effects):
        effects = facts.pd_effects.get(drug_id, []) or []

        for effect in effects:
            effect_id = _effect_id_from_pd_effect(effect)

            if effect_id is None:
                continue

            items.append(
                summarize_pd_effect_claim_coverage(
                    drug_id,
                    effect_id,
                )
            )

    classification_counts = Counter(
        item["classification"]
        for item in items
    )
    coverage_counts = Counter(
        item["coverage_status"]
        for item in items
    )
    confidence_counts = Counter(
        item["confidence_status"]
        for item in items
    )

    return {
        "report_type": "pd_effect_evidence_gap_report",
        "total_pd_effects": len(items),
        "classification_counts": dict(sorted(classification_counts.items())),
        "coverage_counts": dict(sorted(coverage_counts.items())),
        "confidence_counts": dict(sorted(confidence_counts.items())),
        "items": items,
    }