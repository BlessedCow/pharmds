from __future__ import annotations

from core.mechanism_policy import ConcernPolicyResult


def format_policy_result(result: ConcernPolicyResult) -> str:
    """Return a compact human-readable representation of one policy result."""
    if result.target:
        route = (
            f"{result.precipitant_drug} -> {result.object_drug} "
            f"via {result.target}"
        )
    elif result.effect_id:
        route = (
            f"{result.precipitant_drug} + {result.object_drug} "
            f"via {result.effect_id}"
        )
    else:
        route = f"{result.precipitant_drug} -> {result.object_drug}"

    return (
        f"{result.policy_concern}: {route} "
        f"| source_concern={result.source_concern} "
        f"| candidate_type={result.candidate_type} "
        f"| confidence={result.confidence} "
        f"| severity={result.severity}"
    )


def format_policy_results(
    results: list[ConcernPolicyResult],
) -> list[str]:
    """Return compact human-readable representations of policy results."""
    return [format_policy_result(result) for result in results]