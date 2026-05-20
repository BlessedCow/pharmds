"""Evidence completeness reporting helpers."""

from __future__ import annotations

from collections import Counter, defaultdict
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


GAP_CLASSIFICATIONS = {
    COVERAGE_MISSING,
    COVERAGE_CONFLICTING,
    COVERAGE_DISPUTED,
    COVERAGE_UNDETERMINED,
    CONFIDENCE_LOW,
    CONFIDENCE_UNCERTAIN,
    CONFIDENCE_NONE,
}

SOURCE_TYPE_NONE = "no_source"
BACKFILL_PRIORITY_MISSING = "p0_missing_evidence"
BACKFILL_PRIORITY_CONFLICT = "p1_conflict_review"
BACKFILL_PRIORITY_UNDETERMINED = "p2_undetermined_review"
BACKFILL_PRIORITY_CONFIDENCE = "p3_confidence_backfill"

BACKFILL_PREFERRED_SOURCE_TYPES = ("drug_label",)

_BACKFILL_PRIORITY_RANK = {
    BACKFILL_PRIORITY_MISSING: 0,
    BACKFILL_PRIORITY_CONFLICT: 1,
    BACKFILL_PRIORITY_UNDETERMINED: 2,
    BACKFILL_PRIORITY_CONFIDENCE: 3,
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
        "source_types": _source_types_for_claim_traces(claim_traces),
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

    report = {
        "report_type": "pd_effect_evidence_gap_report",
        "total_pd_effects": len(items),
        "classification_counts": dict(sorted(classification_counts.items())),
        "coverage_counts": dict(sorted(coverage_counts.items())),
        "confidence_counts": dict(sorted(confidence_counts.items())),
        "items": items,
    }

    return add_grouped_evidence_gaps(report)


def evidence_gap_items(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Return rows that represent missing or partial evidence coverage."""
    return [
        item
        for item in report.get("items", [])
        if item.get("classification") in GAP_CLASSIFICATIONS
    ]


def _source_types_for_claim_traces(
    claim_traces: list[dict[str, Any]],
) -> list[str]:
    source_types: set[str] = set()

    for claim_trace in claim_traces:
        for evidence in claim_trace.get("evidence", []) or []:
            source = evidence.get("source") or {}
            source_type = source.get("source_type")

            if not source_type:
                source_type = evidence.get("evidence_type")

            if source_type:
                source_types.add(str(source_type))

    if not source_types:
        return [SOURCE_TYPE_NONE]

    return sorted(source_types)


def _empty_grouped_gap_report() -> dict[str, dict[str, list[dict[str, Any]]]]:
    return {
        "by_pd_effect": {},
        "by_drug": {},
        "by_source_type": {},
    }


def group_evidence_gaps(
    report: dict[str, Any],
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    """Group missing/partial evidence rows by effect, drug, and source type."""
    grouped = {
        "by_pd_effect": defaultdict(list),
        "by_drug": defaultdict(list),
        "by_source_type": defaultdict(list),
    }

    for item in evidence_gap_items(report):
        grouped["by_pd_effect"][item["effect_id"]].append(item)
        grouped["by_drug"][item["drug_id"]].append(item)

        source_types = item.get("source_types") or [SOURCE_TYPE_NONE]
        for source_type in source_types:
            grouped["by_source_type"][source_type].append(item)

    if not any(grouped.values()):
        return _empty_grouped_gap_report()

    return {
        group_name: {
            key: sorted(
                values,
                key=lambda item: (
                    item["drug_id"],
                    item["effect_id"],
                    item["classification"],
                ),
            )
            for key, values in sorted(group.items())
        }
        for group_name, group in grouped.items()
    }

def _evidence_gap_priority(item: dict[str, Any]) -> str | None:
    """Classify an evidence item into a maintainer backfill priority."""
    coverage_status = item.get("coverage_status")
    confidence_status = item.get("confidence_status")

    if coverage_status == COVERAGE_MISSING:
        return BACKFILL_PRIORITY_MISSING

    if coverage_status in {COVERAGE_CONFLICTING, COVERAGE_DISPUTED}:
        return BACKFILL_PRIORITY_CONFLICT

    if coverage_status == COVERAGE_UNDETERMINED:
        return BACKFILL_PRIORITY_UNDETERMINED

    if confidence_status in {
        CONFIDENCE_LOW,
        CONFIDENCE_UNCERTAIN,
        CONFIDENCE_NONE,
    }:
        return BACKFILL_PRIORITY_CONFIDENCE

    return None


def _missing_source_types(row: dict[str, Any]) -> list[str]:
    """Return preferred source types still missing for a row."""
    existing_source_types = set(row.get("source_types") or [])
    return [
        source_type
        for source_type in BACKFILL_PREFERRED_SOURCE_TYPES
        if source_type not in existing_source_types
    ]


def _suggested_backfill_action(
    priority: str,
    missing_source_types: list[str],
) -> str:
    """Return a maintainer-facing suggested next action."""
    if priority == BACKFILL_PRIORITY_MISSING:
        return (
            "Add curated evidence claim(s), starting with "
            f"{', '.join(missing_source_types or BACKFILL_PREFERRED_SOURCE_TYPES)}."
        )

    if priority == BACKFILL_PRIORITY_CONFLICT:
        return (
            "Review conflicting or disputed evidence claims and clarify the "
            "preferred curated interpretation."
        )

    if priority == BACKFILL_PRIORITY_UNDETERMINED:
        return (
            "Review source material and assign a supported evidence confidence."
        )

    return (
        "Add stronger or more complete supporting evidence for this drug/effect."
    )


def build_evidence_gap_backfill_plan(
    report: dict[str, Any],
) -> dict[str, Any]:
    """Build prioritized maintainer tasks from evidence gap report items."""
    tasks: list[dict[str, Any]] = []

    for item in report.get("items", []):
        priority = _evidence_gap_priority(item)
        if priority is None:
            continue

        missing_source_types = _missing_source_types(item)
        task = {
            "priority": priority,
            "drug_id": item["drug_id"],
            "effect_id": item["effect_id"],
            "coverage_status": item["coverage_status"],
            "confidence_level": item.get("confidence_level"),
            "confidence_status": item["confidence_status"],
            "classification": item["classification"],
            "claim_count": item["claim_count"],
            "source_types": list(item.get("source_types") or []),
            "missing_source_types": missing_source_types,
            "suggested_next_action": _suggested_backfill_action(
                priority,
                missing_source_types,
            ),
        }
        tasks.append(task)

    tasks.sort(
        key=lambda task: (
            _BACKFILL_PRIORITY_RANK[task["priority"]],
            task["effect_id"],
            task["drug_id"],
            task["classification"],
        )
    )

    by_pd_effect: dict[str, list[dict[str, Any]]] = {}
    by_drug: dict[str, list[dict[str, Any]]] = {}
    priority_counts: dict[str, int] = {}

    for task in tasks:
        by_pd_effect.setdefault(task["effect_id"], []).append(task)
        by_drug.setdefault(task["drug_id"], []).append(task)
        priority_counts[task["priority"]] = (
            priority_counts.get(task["priority"], 0) + 1
        )

    return {
        "total_tasks": len(tasks),
        "priority_counts": dict(sorted(priority_counts.items())),
        "tasks": tasks,
        "by_pd_effect": by_pd_effect,
        "by_drug": by_drug,
    }

def add_grouped_evidence_gaps(
    report: dict[str, Any],
) -> dict[str, Any]:
    """Return report with grouped missing/partial coverage sections."""
    enriched = dict(report)
    grouped = group_evidence_gaps(report)
    
    enriched["gap_count"] = len(evidence_gap_items(report))
    enriched["gaps_by_pd_effect"] = grouped["by_pd_effect"]
    enriched["gaps_by_drug"] = grouped["by_drug"]
    enriched["gaps_by_source_type"] = grouped["by_source_type"]
    enriched["backfill_plan"] = build_evidence_gap_backfill_plan(enriched)
    return enriched