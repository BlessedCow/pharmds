"""Debug formatting helpers for ScoredConcern objects."""

from __future__ import annotations

from typing import Any

from core.evidence.formatting import format_evidence_trace
from core.mechanisms.scoring import ScoredConcern


def _format_debug_evidence_trace(trace: dict[str, Any]) -> list[str]:
    """Return compact debug lines for an evidence trace."""
    formatted_lines = format_evidence_trace(trace)

    if not formatted_lines:
        return []

    debug_lines = ["Evidence:"]

    for line in formatted_lines:
        debug_lines.append(f"  {line}")

    return debug_lines


def format_scored_concern(concern: ScoredConcern) -> str:
    """Return a compact human-readable representation of one scored concern."""
    if concern.target:
        route = (
            f"{concern.precipitant_drug} -> {concern.object_drug} "
            f"via {concern.target}"
        )
    elif concern.effect_id:
        route = (
            f"{concern.precipitant_drug} + {concern.object_drug} "
            f"via {concern.effect_id}"
        )
    else:
        route = f"{concern.precipitant_drug} -> {concern.object_drug}"

    parts = [
        f"{concern.policy_concern}: {route}",
        f"source_concern={concern.source_concern}",
        f"candidate_type={concern.candidate_type}",
        f"confidence={concern.confidence}",
        f"severity={concern.severity}",
    ]

    if concern.aggregate_member_count:
        parts.append(f"aggregate_members={concern.aggregate_member_count}")

    if concern.related_targets:
        parts.append(f"related_targets={', '.join(concern.related_targets)}")

    if concern.related_effects:
        parts.append(f"related_effects={', '.join(concern.related_effects)}")

    summary = " | ".join(parts)

    evidence_trace = concern.metadata.get("evidence_trace")

    if not isinstance(evidence_trace, dict):
        return summary

    evidence_lines = _format_debug_evidence_trace(evidence_trace)

    if not evidence_lines:
        return summary

    return "\n".join([summary, *evidence_lines])


def format_scored_concerns(
    concerns: list[ScoredConcern],
) -> list[str]:
    """Return compact human-readable representations of scored concerns."""
    return [format_scored_concern(concern) for concern in concerns]