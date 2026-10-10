"""Measured PK values retain their formulation, population, and source."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

PKMetric = Literal["half_life", "tmax", "bioavailability", "cmax", "auc"]


@dataclass(frozen=True)
class PKSource:
    id: str
    title: str
    url: str
    evidence_type: str
    revision_date: str | None = None


@dataclass(frozen=True)
class PKObservation:
    id: str
    drug_id: str
    route: str
    release_type: str
    metric: PKMetric
    min_value: float
    max_value: float
    unit: str
    population: str
    analyte: str
    administration_condition: str
    source_id: str
    dose_value: float | None = None
    dose_unit: str | None = None
    notes: str | None = None
    math_eligible: bool = False
