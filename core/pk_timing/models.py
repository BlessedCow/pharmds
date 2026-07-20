from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

TimingUnit = Literal[
    "minutes",
    "hours",
    "days",
]

SteadyStateBasis = Literal[
    "derived_from_half_life",
    "source_reported",
    "unknown",
]


@dataclass(frozen=True)
class TimingRange:
    min_value: float | None
    max_value: float | None
    unit: TimingUnit

    def __post_init__(self) -> None:
        if self.min_value is None and self.max_value is None:
            msg = "TimingRange requires at least one boundary."
            raise ValueError(msg)

        if self.min_value is not None and self.min_value < 0:
            msg = "TimingRange min_value cannot be negative."
            raise ValueError(msg)

        if self.max_value is not None and self.max_value < 0:
            msg = "TimingRange max_value cannot be negative."
            raise ValueError(msg)

        if (
            self.min_value is not None
            and self.max_value is not None
            and self.min_value > self.max_value
        ):
            msg = "TimingRange min_value cannot exceed max_value."
            raise ValueError(msg)


@dataclass(frozen=True)
class PharmacokineticTiming:
    drug_id: str
    route: str
    formulation: str | None = None
    release_type: str | None = None
    half_life: TimingRange | None = None
    tmax: TimingRange | None = None
    onset: TimingRange | None = None
    duration: TimingRange | None = None
    steady_state: TimingRange | None = None
    steady_state_basis: SteadyStateBasis = "unknown"
    active_metabolites: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()