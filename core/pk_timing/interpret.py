from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from core.pk_timing.models import PharmacokineticTiming, TimingRange
from core.pk_timing.resolver import resolve_pk_timing


def describe_timing_range(timing_range: TimingRange | None) -> str | None:
    if timing_range is None:
        return None

    if timing_range.min_value == timing_range.max_value:
        return f"about {_format_number(timing_range.min_value)} {timing_range.unit}"

    if timing_range.min_value is None:
        return f"up to {_format_number(timing_range.max_value)} {timing_range.unit}"

    if timing_range.max_value is None:
        return (
            f"at least {_format_number(timing_range.min_value)} " f"{timing_range.unit}"
        )

    return (
        f"about {_format_number(timing_range.min_value)}-"
        f"{_format_number(timing_range.max_value)} {timing_range.unit}"
    )


def describe_pk_timing(timing: PharmacokineticTiming | None) -> str | None:
    if timing is None:
        return None

    details = []

    peak = describe_timing_range(timing.tmax)
    if peak is not None:
        details.append(f"Peak timing is {peak}")

    half_life = describe_timing_range(timing.half_life)
    if half_life is not None:
        details.append(f"half-life is {half_life}")

    steady_state = describe_timing_range(timing.steady_state)
    if steady_state is not None:
        if timing.steady_state_basis == "derived_from_half_life":
            details.append(
                f"estimated steady state is {steady_state} " "based on half-life"
            )
        else:
            details.append(f"steady state is {steady_state}")

    if not details:
        return None

    return "; ".join(details) + "."


def describe_pk_timing_context(
    drug_ids: Iterable[str],
    *,
    route: str | None = None,
    release_type: str | None = None,
    data: Iterable[PharmacokineticTiming] | None = None,
) -> list[dict[str, Any]]:
    interpretation = []

    for drug_id in drug_ids:
        timing = _resolve_timing(
            drug_id,
            route=route,
            release_type=release_type,
            data=data,
        )

        interpretation.append(
            {
                "drug_id": drug_id,
                "summary": describe_pk_timing(timing),
            }
        )

    return interpretation


def _resolve_timing(
    drug_id: str,
    *,
    route: str | None,
    release_type: str | None,
    data: Iterable[PharmacokineticTiming] | None,
) -> PharmacokineticTiming | None:
    if data is None:
        return resolve_pk_timing(
            drug_id,
            route=route,
            release_type=release_type,
        )

    return resolve_pk_timing(
        drug_id,
        route=route,
        release_type=release_type,
        data=data,
    )


def _format_number(value: float | None) -> str:
    if value is None:
        return ""

    if value.is_integer():
        return str(int(value))

    return str(value)
