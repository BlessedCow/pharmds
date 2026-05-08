from __future__ import annotations

from core.mechanism_arbitration import ArbitrationResult


def format_arbitration_result(result: ArbitrationResult) -> str:
    """Return a compact human-readable representation of one result."""
    if result.target:
        route = f"{result.precipitant_drug} -> {result.object_drug} via {result.target}"
    elif result.effect_id:
        route = f"{result.precipitant_drug} + {result.object_drug} via {result.effect_id}"
    else:
        route = f"{result.precipitant_drug} -> {result.object_drug}"

    return (
        f"{result.concern}: {route} "
        f"| candidate_type={result.candidate_type} "
        f"| confidence={result.confidence} "
        f"| severity={result.severity}"
    )


def format_arbitration_results(
    results: list[ArbitrationResult],
) -> list[str]:
    """Return compact human-readable representations of arbitration results."""
    return [format_arbitration_result(result) for result in results]