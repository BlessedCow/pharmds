"""First-order fractions with structured derivations for educational display."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

PKCalculation = Literal[
    "fraction_remaining", "fraction_to_steady_state", "accumulation_factor"
]
ASSUMPTION = "Constant first-order elimination with one effective half-life."
LIMITATION = (
    "This idealized fraction does not predict a patient concentration, onset, "
    "clinical effect, or risk. Multiphasic and nonlinear kinetics may differ."
)


@dataclass(frozen=True)
class CalculationInput:
    name: str
    value: float
    unit: str


@dataclass(frozen=True)
class CalculationTrace:
    calculation: PKCalculation
    formula: str
    substitutions: str
    inputs: tuple[CalculationInput, ...]
    elimination_rate_per_hour: float
    result: float
    result_unit: str
    assumptions: tuple[str, ...] = (ASSUMPTION,)
    limitations: tuple[str, ...] = (LIMITATION,)
    source_ids: tuple[str, ...] = ()


def _positive_finite(value: float, label: str) -> float:
    if isinstance(value, bool) or not math.isfinite(value) or value <= 0:
        raise ValueError(f"{label} must be positive and finite")
    return value


def _nonnegative_finite(value: float, label: str) -> float:
    if isinstance(value, bool) or not math.isfinite(value) or value < 0:
        raise ValueError(f"{label} must be nonnegative and finite")
    return value


def fraction_remaining(
    half_life_hours: float,
    elapsed_hours: float,
    *,
    source_ids: tuple[str, ...] = (),
) -> CalculationTrace:
    half_life = _positive_finite(half_life_hours, "half_life_hours")
    elapsed = _nonnegative_finite(elapsed_hours, "elapsed_hours")
    k = math.log(2) / half_life
    result = math.exp(-k * elapsed)
    return CalculationTrace(
        calculation="fraction_remaining",
        formula="k = ln(2) / t_half; fraction_remaining = exp(-k * t)",
        substitutions=f"exp(-(ln(2) / {half_life:g} h) * {elapsed:g} h)",
        inputs=(
            CalculationInput("half_life", half_life, "hours"),
            CalculationInput("elapsed", elapsed, "hours"),
        ),
        elimination_rate_per_hour=k,
        result=result,
        result_unit="fraction",
        source_ids=source_ids,
    )


def fraction_to_steady_state(
    half_life_hours: float,
    elapsed_hours: float,
    *,
    source_ids: tuple[str, ...] = (),
) -> CalculationTrace:
    half_life = _positive_finite(half_life_hours, "half_life_hours")
    elapsed = _nonnegative_finite(elapsed_hours, "elapsed_hours")
    k = math.log(2) / half_life
    result = -math.expm1(-k * elapsed)
    return CalculationTrace(
        calculation="fraction_to_steady_state",
        formula="k = ln(2) / t_half; fraction_to_steady_state = 1 - exp(-k * t)",
        substitutions=f"1 - exp(-(ln(2) / {half_life:g} h) * {elapsed:g} h)",
        inputs=(
            CalculationInput("half_life", half_life, "hours"),
            CalculationInput("elapsed", elapsed, "hours"),
        ),
        elimination_rate_per_hour=k,
        result=result,
        result_unit="fraction",
        source_ids=source_ids,
    )


def idealized_accumulation_factor(
    half_life_hours: float,
    interval_hours: float,
    *,
    source_ids: tuple[str, ...] = (),
) -> CalculationTrace:
    half_life = _positive_finite(half_life_hours, "half_life_hours")
    interval = _positive_finite(interval_hours, "interval_hours")
    k = math.log(2) / half_life
    denominator = -math.expm1(-k * interval)
    if denominator == 0:
        raise ValueError("Interval is too small for a finite accumulation factor")
    result = 1 / denominator
    if not math.isfinite(result):
        raise ValueError("Accumulation factor is not finite")
    return CalculationTrace(
        calculation="accumulation_factor",
        formula="k = ln(2) / t_half; accumulation_factor = 1 / (1 - exp(-k * tau))",
        substitutions=f"1 / (1 - exp(-(ln(2) / {half_life:g} h) * {interval:g} h))",
        inputs=(
            CalculationInput("half_life", half_life, "hours"),
            CalculationInput("interval", interval, "hours"),
        ),
        elimination_rate_per_hour=k,
        result=result,
        result_unit="dimensionless",
        limitations=(
            LIMITATION,
            "Assumes equal scheduled doses at a fixed interval; "
            "PRN use does not qualify.",
        ),
        source_ids=source_ids,
    )
