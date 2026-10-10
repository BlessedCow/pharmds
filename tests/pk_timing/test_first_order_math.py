from __future__ import annotations

import math

import pytest

from core.pk_math.first_order import (
    fraction_remaining,
    fraction_to_steady_state,
    idealized_accumulation_factor,
)


def test_reference_fractions_and_trace() -> None:
    remaining = fraction_remaining(8, 8, source_ids=("label-example",))
    steady = fraction_to_steady_state(8, 32)
    assert remaining.result == pytest.approx(0.5)
    assert remaining.elimination_rate_per_hour == pytest.approx(math.log(2) / 8)
    assert remaining.inputs[0].unit == "hours"
    assert "8 h" in remaining.substitutions
    assert remaining.source_ids == ("label-example",)
    assert remaining.result_unit == "fraction"
    assert steady.result == pytest.approx(0.9375)
    assert "1 - exp" in steady.formula


def test_accumulation_factor_for_one_half_life_interval() -> None:
    trace = idealized_accumulation_factor(12, 12)
    assert trace.result == pytest.approx(2)
    assert trace.result_unit == "dimensionless"
    assert any("PRN" in limitation for limitation in trace.limitations)


def test_boundary_and_monotonicity() -> None:
    assert fraction_remaining(5, 0).result == 1
    assert fraction_to_steady_state(5, 0).result == 0
    for hours in (1, 5, 20, 100):
        remaining = fraction_remaining(5, hours).result
        reached = fraction_to_steady_state(5, hours).result
        assert remaining + reached == pytest.approx(1)
        assert 0 <= reached <= 1
    assert idealized_accumulation_factor(12, 6).result > 2
    assert idealized_accumulation_factor(12, 24).result < 2


@pytest.mark.parametrize("invalid", [0, -1, float("nan"), float("inf"), True])
def test_invalid_half_life_is_rejected(invalid: float) -> None:
    with pytest.raises(ValueError):
        fraction_remaining(invalid, 2)
    with pytest.raises(ValueError):
        idealized_accumulation_factor(invalid, 12)


@pytest.mark.parametrize("invalid", [-1, float("nan"), float("inf"), True])
def test_invalid_elapsed_time_is_rejected(invalid: float) -> None:
    with pytest.raises(ValueError):
        fraction_to_steady_state(12, invalid)


@pytest.mark.parametrize("invalid", [0, -1, float("nan"), float("inf"), True])
def test_invalid_interval_is_rejected(invalid: float) -> None:
    with pytest.raises(ValueError):
        idealized_accumulation_factor(12, invalid)
