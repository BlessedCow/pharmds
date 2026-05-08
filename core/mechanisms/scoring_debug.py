"""Debug formatting helpers for ScoredConcern objects."""

from __future__ import annotations

from core.mechanisms.scoring import ScoredConcern


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

    return " | ".join(parts)


def format_scored_concerns(
    concerns: list[ScoredConcern],
) -> list[str]:
    """Return compact human-readable representations of scored concerns."""
    return [format_scored_concern(concern) for concern in concerns]
