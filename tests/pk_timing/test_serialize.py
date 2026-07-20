from core.pk_timing import (
    PharmacokineticTiming,
    TimingRange,
    serialize_pk_timing,
    serialize_timing_range,
)


def test_serialize_timing_range_returns_json_safe_shape() -> None:
    timing_range = TimingRange(
        min_value=1,
        max_value=4,
        unit="hours",
    )

    assert serialize_timing_range(timing_range) == {
        "min_value": 1,
        "max_value": 4,
        "unit": "hours",
    }


def test_serialize_timing_range_handles_none() -> None:
    assert serialize_timing_range(None) is None


def test_serialize_pk_timing_returns_json_safe_shape() -> None:
    timing = PharmacokineticTiming(
        drug_id="example",
        route="oral",
        formulation="tablet",
        release_type="ir",
        half_life=TimingRange(
            min_value=10,
            max_value=12,
            unit="hours",
        ),
        tmax=TimingRange(
            min_value=2,
            max_value=4,
            unit="hours",
        ),
        steady_state=TimingRange(
            min_value=40,
            max_value=60,
            unit="hours",
        ),
        steady_state_basis="derived_from_half_life",
        active_metabolites=("active-metabolite",),
        notes=("Example timing note.",),
    )

    assert serialize_pk_timing(timing) == {
        "drug_id": "example",
        "route": "oral",
        "formulation": "tablet",
        "release_type": "ir",
        "half_life": {
            "min_value": 10,
            "max_value": 12,
            "unit": "hours",
        },
        "tmax": {
            "min_value": 2,
            "max_value": 4,
            "unit": "hours",
        },
        "onset": None,
        "duration": None,
        "steady_state": {
            "min_value": 40,
            "max_value": 60,
            "unit": "hours",
        },
        "steady_state_basis": "derived_from_half_life",
        "active_metabolites": ["active-metabolite"],
        "notes": ["Example timing note."],
    }


def test_serialize_pk_timing_handles_none() -> None:
    assert serialize_pk_timing(None) is None