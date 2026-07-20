import pytest

from core.pk_timing import TimingRange, estimate_steady_state


def test_estimate_steady_state_uses_four_to_five_half_lives() -> None:
    half_life = TimingRange(
        min_value=10,
        max_value=12,
        unit="hours",
    )

    steady_state = estimate_steady_state(half_life)

    assert steady_state == TimingRange(
        min_value=40,
        max_value=60,
        unit="hours",
    )


def test_estimate_steady_state_handles_single_point_half_life() -> None:
    half_life = TimingRange(
        min_value=24,
        max_value=None,
        unit="hours",
    )

    steady_state = estimate_steady_state(half_life)

    assert steady_state == TimingRange(
        min_value=96,
        max_value=120,
        unit="hours",
    )


def test_estimate_steady_state_returns_none_without_half_life() -> None:
    assert estimate_steady_state(None) is None


def test_timing_range_requires_at_least_one_boundary() -> None:
    with pytest.raises(ValueError, match="requires at least one boundary"):
        TimingRange(
            min_value=None,
            max_value=None,
            unit="hours",
        )


def test_timing_range_rejects_negative_values() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        TimingRange(
            min_value=-1,
            max_value=2,
            unit="hours",
        )


def test_timing_range_rejects_inverted_ranges() -> None:
    with pytest.raises(ValueError, match="cannot exceed"):
        TimingRange(
            min_value=12,
            max_value=10,
            unit="hours",
        )