from __future__ import annotations

from typing import Any

from core.evidence.conflicts import (
    EVIDENCE_SUPPORT_CONFLICTING,
    EVIDENCE_SUPPORT_DISPUTED,
    EVIDENCE_SUPPORT_SUPPORTED,
)
from core.evidence.traces import build_pd_effect_traces_for_drug_effect


def _evidence_status_for_drug_traces(
    drug_traces: list[dict[str, Any]],
) -> str:
    statuses = {
        trace.get("evidence_support_status")
        for trace in drug_traces
    }

    if EVIDENCE_SUPPORT_CONFLICTING in statuses:
        return "conflicting"

    if (
        EVIDENCE_SUPPORT_SUPPORTED in statuses
        and EVIDENCE_SUPPORT_DISPUTED in statuses
    ):
        return "conflicting"

    if EVIDENCE_SUPPORT_SUPPORTED in statuses:
        return "present"

    if EVIDENCE_SUPPORT_DISPUTED in statuses:
        return "disputed"

    if drug_traces:
        return "undetermined"

    return "missing"


def _overall_evidence_status(
    drug_trace_items: list[dict[str, Any]],
) -> str:
    statuses = {
        item["evidence_status"]
        for item in drug_trace_items
    }

    if "conflicting" in statuses:
        return "conflicting"

    if statuses == {"present"}:
        return "complete"

    if "present" in statuses:
        return "partial"

    if "disputed" in statuses:
        return "disputed"

    return "missing"


def build_additive_pd_effect_evidence_trace(
    drug_ids: list[str],
    effect_id: str,
) -> dict[str, Any]:
    drug_trace_items = []

    for drug_id in drug_ids:
        traces = build_pd_effect_traces_for_drug_effect(
            drug_id,
            effect_id,
        )

        drug_trace_items.append(
            {
                "drug_id": drug_id,
                "effect_id": effect_id,
                "evidence_status": _evidence_status_for_drug_traces(traces),
                "claims": traces,
            }
        )

    return {
        "trace_type": "additive_pd_effect",
        "effect_id": effect_id,
        "drug_ids": drug_ids,
        "overall_evidence_status": _overall_evidence_status(
            drug_trace_items,
        ),
        "drugs": drug_trace_items,
    }


def build_additive_pd_effect_evidence_traces(
    drug_ids: list[str],
    effect_ids: list[str],
) -> list[dict[str, Any]]:
    return [
        build_additive_pd_effect_evidence_trace(
            drug_ids,
            effect_id,
        )
        for effect_id in effect_ids
    ]