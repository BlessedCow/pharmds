"""Streamlit-facing summary formatting helpers.

These helpers intentionally avoid importing Streamlit so they can be tested
with normal unit tests.
"""

from __future__ import annotations

from typing import Any

from core.mechanisms.result_summary import ResultSummary

MISSING_LABEL = "not_available"


def _human_join(items: list[str] | tuple[str, ...]) -> str:
    values = [str(item) for item in items if item]

    if not values:
        return "No drugs listed"

    if len(values) == 1:
        return values[0]

    if len(values) == 2:
        return f"{values[0]} and {values[1]}"

    return f"{', '.join(values[:-1])}, and {values[-1]}"


def _clean_label(value: Any, *, fallback: str = MISSING_LABEL) -> str:
    if value is None:
        return fallback

    text = str(value).strip()

    if not text:
        return fallback

    return text


def result_summary_to_streamlit_card(
    summary: ResultSummary,
) -> dict[str, Any]:
    """Convert a public result summary into a small UI card payload."""
    return {
        "source": summary.source,
        "title": _clean_label(summary.title, fallback="Summary"),
        "drugs": _human_join(summary.drugs),
        "concern_type": _clean_label(summary.concern_type),
        "severity_label": _clean_label(summary.severity_label),
        "evidence_label": _clean_label(summary.evidence_label),
        "explanation": _clean_label(
            summary.explanation,
            fallback="No explanation available.",
        ),
    }


def result_summaries_to_streamlit_cards(
    summaries: list[ResultSummary],
    *,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Convert public result summaries into display-ready card payloads."""
    cards = [
        result_summary_to_streamlit_card(summary)
        for summary in summaries
    ]

    if limit is None:
        return cards

    return cards[:limit]


def aggregate_summary_debug_fields(
    aggregate_summary: dict[str, Any],
) -> dict[str, Any]:
    """Extract compact aggregate/evidence details for an expander."""
    aggregate = aggregate_summary.get("aggregate") or {}
    evidence = aggregate_summary.get("evidence_summary") or {}
    severity = aggregate_summary.get("severity_annotation") or {}

    return {
        "aggregate_type": _clean_label(aggregate.get("aggregate_type")),
        "policy_concern": _clean_label(aggregate.get("policy_concern")),
        "anchor": _clean_label(aggregate.get("anchor")),
        "effect_id": _clean_label(aggregate.get("effect_id")),
        "targets": list(aggregate.get("targets") or []),
        "severity": _clean_label(
            severity.get("strongest_preliminary_severity"),
        ),
        "evidence_status": _clean_label(
            evidence.get("overall_evidence_status"),
        ),
        "evidence_claim_count": evidence.get("evidence_claim_count", 0),
        "evidence_gap_count": evidence.get("evidence_gap_count", 0),
        "evidence_trace_count": evidence.get("evidence_trace_count", 0),
        "patient_risk_modifiers": list(
            aggregate_summary.get("patient_risk_modifiers") or []
        ),
        "risk_context": aggregate_summary.get("risk_context"),
        "evidence_conflict_level": aggregate_summary.get(
            "evidence_conflict_level"
        ),
        "evidence_conflict_message": aggregate_summary.get(
            "evidence_conflict_message"
        ),
    }


def aggregate_summary_debug_lines(
    aggregate_summary: dict[str, Any],
) -> list[str]:
    """Return human-readable aggregate details for Streamlit expanders."""
    fields = aggregate_summary_debug_fields(aggregate_summary)

    lines = [
        f"Aggregate type: {fields['aggregate_type']}",
        f"Concern: {fields['policy_concern']}",
        f"Anchor: {fields['anchor']}",
        f"Effect: {fields['effect_id']}",
        f"Severity: {fields['severity']}",
        f"Evidence status: {fields['evidence_status']}",
        f"Evidence claims: {fields['evidence_claim_count']}",
        f"Evidence gaps: {fields['evidence_gap_count']}",
        f"Evidence traces: {fields['evidence_trace_count']}",
    ]

    if fields["targets"]:
        lines.append(f"Targets: {', '.join(fields['targets'])}")

    if fields["patient_risk_modifiers"]:
        modifiers = ", ".join(fields["patient_risk_modifiers"])
        lines.append(f"Patient risk modifiers: {modifiers}")

    if fields["risk_context"]:
        lines.append(f"Risk context: {fields['risk_context']}")

    if fields["evidence_conflict_message"]:
        lines.append(
            "Evidence conflict: "
            f"{fields['evidence_conflict_message']}"
        )

    return lines