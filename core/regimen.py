from __future__ import annotations

import math
import re
from dataclasses import dataclass

DAYPART_FREQUENCIES: dict[str, str] = {
    "qam": "morning",
    "qpm": "evening",
    "qhs": "bedtime",
}

DAILY_COUNT_FREQUENCIES: dict[str, float] = {
    "qd": 1.0,
    "bid": 2.0,
    "tid": 3.0,
    "qid": 4.0,
}

WEEKLY_FREQUENCIES: dict[str, float] = {
    "qwk": 1.0,
    "tiw": 3.0,
}

MEAL_RELATIVE_FREQUENCIES: dict[str, str] = {
    "ac": "before_meals",
    "qac": "before_meals",
    "pc": "after_meals",
    "qpc": "after_meals",
}

FREQUENCY_ALIASES: dict[str, str] = {
    "daily": "qd",
    "qday": "qd",
    "hs": "qhs",
    "weekly": "qwk",
}

AMBIGUOUS_FREQUENCIES = frozenset({"biw"})
_Q_HOUR_RE = re.compile(r"^q(?P<hours>\d+(?:\.\d+)?)h$")


@dataclass(frozen=True)
class FrequencyProfile:
    code: str
    timing_type: str
    administrations_per_day: float | None = None
    prn_max_administrations_per_day: float | None = None
    interval_hours: float | None = None
    daypart: str | None = None
    administrations_per_week: float | None = None
    calendar_interval_days: float | None = None
    meal_relation: str | None = None
    ambiguous: bool = False


@dataclass(frozen=True)
class RegimenDose:
    dose_value: float
    dose_unit: str
    frequency: str | None = None
    schedule_type: str = "scheduled"
    administrations_per_day: float | None = None
    max_administrations_per_day: float | None = None

    @property
    def frequency_profile(self) -> FrequencyProfile | None:
        return frequency_profile(self.frequency)

    @property
    def frequency_code(self) -> str | None:
        profile = self.frequency_profile
        return profile.code if profile is not None else None

    @property
    def timing_type(self) -> str | None:
        profile = self.frequency_profile
        return profile.timing_type if profile is not None else None

    @property
    def interval_hours(self) -> float | None:
        profile = self.frequency_profile
        return profile.interval_hours if profile is not None else None

    @property
    def daypart(self) -> str | None:
        profile = self.frequency_profile
        return profile.daypart if profile is not None else None

    @property
    def meal_relation(self) -> str | None:
        profile = self.frequency_profile
        return profile.meal_relation if profile is not None else None

    @property
    def around_the_clock(self) -> bool:
        return (
            self.schedule_type == "scheduled"
            and self.timing_type == "fixed_interval"
        )

    @property
    def inferred_administrations_per_day(self) -> float | None:
        if self.administrations_per_day is not None:
            return self.administrations_per_day
        profile = self.frequency_profile
        if profile is None:
            return None
        return profile.administrations_per_day

    @property
    def inferred_prn_max_administrations_per_day(self) -> float | None:
        if self.max_administrations_per_day is not None:
            return self.max_administrations_per_day
        profile = self.frequency_profile
        if profile is None:
            return None
        return profile.prn_max_administrations_per_day

    @property
    def scheduled_daily_dose(self) -> float | None:
        if self.schedule_type != "scheduled":
            return None
        administrations = self.inferred_administrations_per_day
        if administrations is None:
            return None
        return self.dose_value * administrations

    @property
    def prn_max_daily_dose(self) -> float | None:
        if self.schedule_type != "prn":
            return None
        administrations = self.inferred_prn_max_administrations_per_day
        if administrations is None:
            return None
        return self.dose_value * administrations


def normalize_frequency(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().casefold().replace(" ", "").replace(".", "")
    if not normalized:
        return None
    return FREQUENCY_ALIASES.get(normalized, normalized)


def frequency_profile(value: str | None) -> FrequencyProfile | None:
    code = normalize_frequency(value)
    if code is None:
        return None

    if code in DAYPART_FREQUENCIES:
        return FrequencyProfile(
            code=code,
            timing_type="daypart",
            administrations_per_day=1.0,
            prn_max_administrations_per_day=1.0,
            daypart=DAYPART_FREQUENCIES[code],
        )

    if code in DAILY_COUNT_FREQUENCIES:
        administrations = DAILY_COUNT_FREQUENCIES[code]
        return FrequencyProfile(
            code=code,
            timing_type="daily_count",
            administrations_per_day=administrations,
            prn_max_administrations_per_day=administrations,
        )

    match = _Q_HOUR_RE.fullmatch(code)
    if match is not None:
        interval_hours = float(match.group("hours"))
        if interval_hours <= 0:
            return FrequencyProfile(code=code, timing_type="custom")
        return FrequencyProfile(
            code=code,
            timing_type="fixed_interval",
            administrations_per_day=24.0 / interval_hours,
            prn_max_administrations_per_day=float(
                math.ceil(24.0 / interval_hours)
            ),
            interval_hours=interval_hours,
        )

    if code == "qod":
        return FrequencyProfile(
            code=code,
            timing_type="calendar_interval",
            calendar_interval_days=2.0,
        )

    if code in WEEKLY_FREQUENCIES:
        return FrequencyProfile(
            code=code,
            timing_type="weekly",
            administrations_per_week=WEEKLY_FREQUENCIES[code],
        )

    if code == "qmonth":
        return FrequencyProfile(code=code, timing_type="calendar_interval")

    if code in MEAL_RELATIVE_FREQUENCIES:
        return FrequencyProfile(
            code=code,
            timing_type="meal_relative",
            meal_relation=MEAL_RELATIVE_FREQUENCIES[code],
        )

    if code in AMBIGUOUS_FREQUENCIES:
        return FrequencyProfile(
            code=code,
            timing_type="custom",
            ambiguous=True,
        )

    return FrequencyProfile(code=code, timing_type="custom")


def frequency_administrations_per_day(value: str | None) -> float | None:
    profile = frequency_profile(value)
    if profile is None:
        return None
    return profile.administrations_per_day
