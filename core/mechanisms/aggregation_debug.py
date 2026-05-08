from __future__ import annotations

from core.mechanisms.aggregation import AggregateConcern


def format_aggregate_concern(concern: AggregateConcern) -> str:
    """Return a compact human-readable representation of one aggregate."""
    parts = [
        f"{concern.aggregate_type}: {concern.anchor}",
        f"policy_concern={concern.policy_concern}",
        f"drugs={', '.join(concern.drugs)}",
    ]

    if concern.targets:
        parts.append(f"targets={', '.join(concern.targets)}")

    if concern.effect_id:
        parts.append(f"effect={concern.effect_id}")

    parts.append(f"members={len(concern.members)}")

    return " | ".join(parts)


def format_aggregate_concerns(
    concerns: list[AggregateConcern],
) -> list[str]:
    """Return compact human-readable representations of aggregates."""
    return [format_aggregate_concern(concern) for concern in concerns]
