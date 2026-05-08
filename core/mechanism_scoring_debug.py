"""Debug formatting helpers for ScoredConcern objects."""

from __future__ import annotations

from core.mechanism_scoring import ScoredConcern


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

    return (
        f"{concern.policy_concern}: {route} "
        f"| source_concern={concern.source_concern} "
        f"| candidate_type={concern.candidate_type} "
        f"| confidence={concern.confidence} "
        f"| severity={concern.severity}"
    )


def format_scored_concerns(
    concerns: list[ScoredConcern],
) -> list[str]:
    """Return compact human-readable representations of scored concerns."""
    return [format_scored_concern(concern) for concern in concerns]