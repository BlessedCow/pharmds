from core.pk_timing import (
    PharmacokineticTiming,
    TimingRange,
    resolve_pk_timing,
)


def test_resolve_pk_timing_uses_exact_route_and_release_match() -> None:
    timing = resolve_pk_timing(
        "propranolol",
        route="oral",
        release_type="er",
    )

    assert timing is not None
    assert timing.drug_id == "propranolol"
    assert timing.route == "oral"
    assert timing.release_type == "er"
    assert timing.tmax == TimingRange(
        min_value=6,
        max_value=10,
        unit="hours",
    )


def test_resolve_pk_timing_falls_back_to_route_match() -> None:
    timing = resolve_pk_timing(
        "propranolol",
        route="oral",
    )

    assert timing is not None
    assert timing.drug_id == "propranolol"
    assert timing.route == "oral"
    assert timing.release_type == "ir"


def test_resolve_pk_timing_falls_back_to_drug_match() -> None:
    timing = resolve_pk_timing(
        "propranolol",
        route="iv",
        release_type="unknown",
    )

    assert timing is not None
    assert timing.drug_id == "propranolol"
    assert timing.route == "oral"
    assert timing.release_type == "ir"


def test_resolve_pk_timing_returns_none_for_unknown_drug() -> None:
    assert resolve_pk_timing("notarealdrug") is None


def test_resolve_pk_timing_normalizes_lookup_values() -> None:
    timing = resolve_pk_timing(
        " Propranolol ",
        route=" Oral ",
        release_type=" ER ",
    )

    assert timing is not None
    assert timing.release_type == "er"


def test_resolve_pk_timing_derives_steady_state_when_missing() -> None:
    timing = resolve_pk_timing("propranolol", route="oral", release_type="ir")

    assert timing is not None
    assert timing.steady_state == TimingRange(
        min_value=12,
        max_value=30,
        unit="hours",
    )
    assert timing.steady_state_basis == "derived_from_half_life"


def test_resolve_pk_timing_preserves_source_reported_steady_state() -> None:
    timing = resolve_pk_timing("vortioxetine", route="oral", release_type="ir")

    assert timing is not None
    assert timing.steady_state == TimingRange(
        min_value=14,
        max_value=14,
        unit="days",
    )
    assert timing.steady_state_basis == "source_reported"


def test_resolve_pk_timing_accepts_custom_data() -> None:
    custom_timing = PharmacokineticTiming(
        drug_id="example",
        route="oral",
        release_type="ir",
        half_life=TimingRange(
            min_value=1,
            max_value=2,
            unit="hours",
        ),
    )

    timing = resolve_pk_timing(
        "example",
        route="oral",
        release_type="ir",
        data=(custom_timing,),
    )

    assert timing is not None
    assert timing.steady_state == TimingRange(
        min_value=4,
        max_value=10,
        unit="hours",
    )