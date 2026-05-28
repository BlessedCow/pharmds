"""Streamlit-facing summary formatting helpers.

These helpers intentionally avoid importing Streamlit so they can be tested
with normal unit tests.
"""

from __future__ import annotations

from typing import Any

from core.evidence.loader import get_source_by_id
from core.mechanisms.effect_labels import effect_display_label
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

def _format_effect_value(effect_id: Any) -> str:
    effect = _clean_label(effect_id)

    if effect == MISSING_LABEL:
        return effect

    label = effect_display_label(effect)
    if label == effect:
        return effect

    return f"{effect} ({label})"

def _format_evidence_source_label(source_id: str) -> str:
    source = get_source_by_id(source_id)

    if not source:
        return source_id

    title = source.get("title") or source_id
    source_type = source.get("source_type")

    if source_type:
        return f"{title} ({source_type})"

    return str(title)


def _format_evidence_sources(source_ids: list[str]) -> str:
    if not source_ids:
        return "none"

    noun = "source" if len(source_ids) == 1 else "sources"
    labels = [
        _format_evidence_source_label(source_id)
        for source_id in source_ids
    ]

    return f"{len(source_ids)} {noun}: " + ", ".join(labels)

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


def _summary_value(source: Any, field: str, default: Any = None) -> Any:
    """Read a field from dict or dataclass-style summary objects."""
    if source is None:
        return default

    if isinstance(source, dict):
        return source.get(field, default)

    return getattr(source, field, default)


def aggregate_summary_debug_fields(
    aggregate_summary: Any,
) -> dict[str, Any]:
    """Extract compact aggregate/evidence details for an expander."""
    aggregate = _summary_value(aggregate_summary, "aggregate", {})
    evidence = _summary_value(aggregate_summary, "evidence_summary", {})
    severity = _summary_value(
        aggregate_summary,
        "severity_annotation",
        {},
    )

    return {
        "aggregate_type": _clean_label(
            _summary_value(aggregate, "aggregate_type")
        ),
        "policy_concern": _clean_label(
            _summary_value(aggregate, "policy_concern")
        ),
        "anchor": _clean_label(_summary_value(aggregate, "anchor")),
        "effect_id": _clean_label(_summary_value(aggregate, "effect_id")),
        "effect_label": _format_effect_value(
            _summary_value(aggregate, "effect_id")
            or _summary_value(aggregate, "anchor")
        ),
        "targets": list(_summary_value(aggregate, "targets", ()) or []),
        "severity": _clean_label(
            _summary_value(severity, "strongest_preliminary_severity"),
        ),
        "evidence_status": _clean_label(
            _summary_value(evidence, "overall_evidence_status"),
        ),
        "evidence_claim_count": _summary_value(
            evidence,
            "evidence_claim_count",
            0,
        ),
        "evidence_gap_count": _summary_value(
            evidence,
            "evidence_gap_count",
            0,
        ),
        "evidence_trace_count": _summary_value(
            evidence,
            "evidence_trace_count",
            0,
        ),
        "evidence_source_ids": list(
            _summary_value(
                evidence,
                "evidence_source_ids",
                (),
            )
            or []
        ),
        "patient_risk_modifiers": list(
            _summary_value(
                aggregate_summary,
                "patient_risk_modifiers",
                (),
            )
            or []
        ),
        "risk_context": _summary_value(aggregate_summary, "risk_context"),
        "evidence_conflict_level": _summary_value(
            aggregate_summary,
            "evidence_conflict_level",
        ),
        "evidence_conflict_message": _summary_value(
            aggregate_summary,
            "evidence_conflict_message",
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
        f"Effect: {fields['effect_label']}",
        f"Severity: {fields['severity']}",
        f"Evidence status: {fields['evidence_status']}",
        f"Evidence claims: {fields['evidence_claim_count']}",
        f"Evidence gaps: {fields['evidence_gap_count']}",
        f"Evidence traces: {fields['evidence_trace_count']}",
        "Evidence sources: "
        + _format_evidence_sources(fields["evidence_source_ids"]),
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