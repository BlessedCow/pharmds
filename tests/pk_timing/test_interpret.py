from core.pk_timing import (
    PharmacokineticTiming,
    TimingRange,
    describe_pk_timing,
    describe_pk_timing_context,
    describe_pk_timing_context_from_entries,
    describe_timing_range,
)


def test_describe_timing_range_handles_point_value() -> None:
    assert (
        describe_timing_range(
            TimingRange(
                min_value=14,
                max_value=14,
                unit="days",
            )
        )
        == "about 14 days"
    )


def test_describe_timing_range_handles_range_value() -> None:
    assert (
        describe_timing_range(
            TimingRange(
                min_value=7,
                max_value=11,
                unit="hours",
            )
        )
        == "about 7-11 hours"
    )


def test_describe_timing_range_handles_upper_bound_only() -> None:
    assert (
        describe_timing_range(
            TimingRange(
                min_value=None,
                max_value=6,
                unit="hours",
            )
        )
        == "up to 6 hours"
    )


def test_describe_timing_range_handles_lower_bound_only() -> None:
    assert (
        describe_timing_range(
            TimingRange(
                min_value=6,
                max_value=None,
                unit="hours",
            )
        )
        == "at least 6 hours"
    )


def test_describe_pk_timing_includes_peak_half_life_and_steady_state() -> None:
    timing = PharmacokineticTiming(
        drug_id="example",
        route="oral",
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
    )

    assert describe_pk_timing(timing) == (
        "Peak timing is about 2-4 hours; half-life is about "
        "10-12 hours; estimated steady state is about 40-60 "
        "hours based on half-life."
    )


def test_describe_pk_timing_returns_none_without_timing_details() -> None:
    timing = PharmacokineticTiming(
        drug_id="example",
        route="oral",
    )

    assert describe_pk_timing(timing) is None


def test_describe_pk_timing_context_returns_drug_summaries() -> None:
    context = describe_pk_timing_context(
        ["vortioxetine", "propranolol"],
        route="oral",
        release_type="ir",
    )

    assert context[0] == {
        "drug_id": "vortioxetine",
        "summary": (
            "Peak timing is about 7-11 hours; half-life is about "
            "66 hours; steady state is about 14 days."
        ),
    }
    assert context[1] == {
        "drug_id": "propranolol",
        "summary": (
            "Peak timing is about 1-4 hours; half-life is about "
            "3-6 hours; estimated steady state is about 12-30 "
            "hours based on half-life."
        ),
    }


def test_describe_pk_timing_context_from_entries_uses_per_drug_timing() -> None:
    context = describe_pk_timing_context_from_entries(
        [
            {
                "drug_id": "propranolol",
                "route": "oral",
                "release_type": "er",
            },
            {
                "drug_id": "vortioxetine",
                "route": "oral",
                "release_type": "ir",
            },
        ]
    )

    assert context[0] == {
        "drug_id": "propranolol",
        "summary": (
            "Peak timing is about 6-10 hours; half-life is about 8-10 hours; "
            "estimated steady state is about 32-50 hours based on half-life."
        ),
    }
    assert context[1] == {
        "drug_id": "vortioxetine",
        "summary": (
            "Peak timing is about 7-11 hours; half-life is about 66 hours; "
            "steady state is about 14 days."
        ),
    }


def test_describe_pk_timing_context_returns_none_summary_for_unknown_drug() -> None:
    context = describe_pk_timing_context(["notarealdrug"])

    assert context == [
        {
            "drug_id": "notarealdrug",
            "summary": None,
        }
    ]