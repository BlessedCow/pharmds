from core.regimen import (
    RegimenDose,
    frequency_administrations_per_day,
    frequency_profile,
    normalize_frequency,
)


def test_qam_and_qhs_share_count_but_preserve_daypart() -> None:
    qam = RegimenDose(2, "mg", frequency="QAM")
    qhs = RegimenDose(2, "mg", frequency="HS")

    assert qam.scheduled_daily_dose == 2
    assert qhs.scheduled_daily_dose == 2
    assert qam.timing_type == "daypart"
    assert qhs.timing_type == "daypart"
    assert qam.daypart == "morning"
    assert qhs.daypart == "bedtime"
    assert qhs.frequency_code == "qhs"


def test_tid_and_q8h_keep_different_schedule_semantics() -> None:
    tid = RegimenDose(2, "mg", frequency="TID")
    q8h = RegimenDose(2, "mg", frequency="Q8H")

    assert tid.scheduled_daily_dose == 6
    assert q8h.scheduled_daily_dose == 6
    assert tid.timing_type == "daily_count"
    assert tid.interval_hours is None
    assert not tid.around_the_clock
    assert q8h.timing_type == "fixed_interval"
    assert q8h.interval_hours == 8
    assert q8h.around_the_clock


def test_prn_q4h_is_not_scheduled_exposure() -> None:
    regimen = RegimenDose(2, "mg", frequency="Q4H", schedule_type="prn")

    assert regimen.scheduled_daily_dose is None
    assert regimen.prn_max_daily_dose == 12
    assert not regimen.around_the_clock
    assert regimen.timing_type == "fixed_interval"
    assert regimen.interval_hours == 4


def test_explicit_prn_max_overrides_frequency_ceiling() -> None:
    regimen = RegimenDose(
        2,
        "mg",
        frequency="Q4H",
        schedule_type="prn",
        max_administrations_per_day=3,
    )

    assert regimen.prn_max_daily_dose == 6


def test_fixed_interval_frequency_supports_nonstandard_hour_interval() -> None:
    profile = frequency_profile("Q5H")

    assert profile is not None
    assert profile.timing_type == "fixed_interval"
    assert profile.interval_hours == 5
    assert profile.administrations_per_day == 24 / 5
    assert profile.prn_max_administrations_per_day == 5


def test_weekly_and_calendar_frequencies_do_not_fake_daily_dose() -> None:
    weekly = RegimenDose(10, "mg", frequency="QWK")
    qod = RegimenDose(10, "mg", frequency="QOD")

    assert weekly.timing_type == "weekly"
    assert weekly.scheduled_daily_dose is None
    assert qod.timing_type == "calendar_interval"
    assert qod.scheduled_daily_dose is None


def test_meal_relative_frequency_preserves_relation_without_daily_count() -> None:
    profile = frequency_profile("AC")

    assert profile is not None
    assert profile.timing_type == "meal_relative"
    assert profile.meal_relation == "before_meals"
    assert profile.administrations_per_day is None


def test_biw_is_preserved_but_marked_ambiguous() -> None:
    profile = frequency_profile("BIW")

    assert profile is not None
    assert profile.code == "biw"
    assert profile.timing_type == "custom"
    assert profile.ambiguous


def test_common_frequency_normalization() -> None:
    assert normalize_frequency(" q.a.m. ") == "qam"
    assert normalize_frequency("HS") == "qhs"
    assert normalize_frequency("daily") == "qd"
    assert frequency_administrations_per_day(" q12h ") == 2
