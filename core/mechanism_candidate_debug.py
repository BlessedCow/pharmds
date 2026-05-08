from __future__ import annotations

from core.mechanism_candidates import InteractionCandidate


def format_interaction_candidate(candidate: InteractionCandidate) -> str:
    """Return a compact human-readable representation of one candidate."""
    if candidate.target:
        return (
            f"{candidate.candidate_type}: "
            f"{candidate.precipitant_drug} -> {candidate.object_drug} "
            f"via {candidate.target}"
        )

    if candidate.effect_id:
        return (
            f"{candidate.candidate_type}: "
            f"{candidate.precipitant_drug} + {candidate.object_drug} "
            f"via {candidate.effect_id}"
        )

    return (
        f"{candidate.candidate_type}: "
        f"{candidate.precipitant_drug} -> {candidate.object_drug}"
    )


def format_interaction_candidates(
    candidates: list[InteractionCandidate],
) -> list[str]:
    """Return compact human-readable representations of candidates."""
    return [
        format_interaction_candidate(candidate)
        for candidate in candidates
    ]