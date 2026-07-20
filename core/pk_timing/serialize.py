from __future__ import annotations

from typing import Any

from core.pk_timing.models import PharmacokineticTiming, TimingRange


def serialize_timing_range(
    timing_range: TimingRange | None,
) -> dict[str, Any] | None:
    if timing_range is None:
        return None

    return {
        "min_value": timing_range.min_value,
        "max_value": timing_range.max_value,
        "unit": timing_range.unit,
    }


def serialize_pk_timing(
    timing: PharmacokineticTiming | None,
) -> dict[str, Any] | None:
    if timing is None:
        return None

    return {
        "drug_id": timing.drug_id,
        "route": timing.route,
        "formulation": timing.formulation,
        "release_type": timing.release_type,
        "half_life": serialize_timing_range(timing.half_life),
        "tmax": serialize_timing_range(timing.tmax),
        "onset": serialize_timing_range(timing.onset),
        "duration": serialize_timing_range(timing.duration),
        "steady_state": serialize_timing_range(timing.steady_state),
        "steady_state_basis": timing.steady_state_basis,
        "active_metabolites": list(timing.active_metabolites),
        "notes": list(timing.notes),
    }