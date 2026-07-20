from __future__ import annotations

from core.pk_timing.models import TimingRange

STEADY_STATE_HALF_LIFE_MULTIPLIER_MIN = 4
STEADY_STATE_HALF_LIFE_MULTIPLIER_MAX = 5


def estimate_steady_state(half_life: TimingRange | None) -> TimingRange | None:
    if half_life is None:
        return None

    min_boundary = half_life.min_value
    max_boundary = half_life.max_value

    if min_boundary is None:
        min_boundary = max_boundary

    if max_boundary is None:
        max_boundary = min_boundary

    if min_boundary is None or max_boundary is None:
        return None

    return TimingRange(
        min_value=min_boundary * STEADY_STATE_HALF_LIFE_MULTIPLIER_MIN,
        max_value=max_boundary * STEADY_STATE_HALF_LIFE_MULTIPLIER_MAX,
        unit=half_life.unit,
    )