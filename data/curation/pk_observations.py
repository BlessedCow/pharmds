"""Validate and load sourced PK measurements independently from interaction rules."""

from __future__ import annotations

import json
import math
from datetime import date
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlparse

from core.formulations import RELEASE_TYPE_OPTIONS, ROUTE_OPTIONS
from core.pk_observations.models import PKMetric, PKObservation, PKSource
from data.loaders import load_drugs_curation

DEFAULT_PATH = Path(__file__).with_suffix(".json")
METRIC_UNITS = {
    "half_life": "hours",
    "tmax": "hours",
    "bioavailability": "fraction",
    "cmax": "ng/mL",
    "auc": "ng*h/mL",
}
EVIDENCE_TYPES = {"prescribing_label", "clinical_study", "review"}


def _required_text(row: dict[str, Any], key: str, path: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{path}.{key} must be a nonempty string")
    return value.strip()


def _number(row: dict[str, Any], key: str, path: str) -> float:
    value = row.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{path}.{key} must be a finite number")
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{path}.{key} must be finite and nonnegative")
    return number


def load_pk_curation(
    path: Path = DEFAULT_PATH,
    *,
    drugs_path: Path | None = None,
) -> tuple[tuple[PKSource, ...], tuple[PKObservation, ...]]:
    """Reject ambiguous, unsourced, or formulation-mismatched measurements."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("version") != 1:
        raise ValueError("PK curation requires version 1")
    if not isinstance(raw.get("sources"), list) or not isinstance(
        raw.get("observations"), list
    ):
        raise ValueError("PK sources and observations must be lists")

    drug_data = load_drugs_curation(drugs_path)
    formulations = {
        (drug["id"], form["route"], release)
        for drug in drug_data["drugs"]
        for form in drug.get("formulations", []) or []
        for release in form.get("release_types", []) or []
    }
    sources: list[PKSource] = []
    source_ids: set[str] = set()
    for index, row in enumerate(raw["sources"]):
        path_label = f"sources[{index}]"
        if not isinstance(row, dict):
            raise ValueError(f"{path_label} must be an object")
        source_id = _required_text(row, "id", path_label)
        if source_id in source_ids:
            raise ValueError(f"Duplicate PK source: {source_id}")
        url = _required_text(row, "url", path_label)
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError(f"{path_label}.url requires an HTTPS URL")
        evidence_type = _required_text(row, "evidence_type", path_label)
        if evidence_type not in EVIDENCE_TYPES:
            raise ValueError(f"{path_label}.evidence_type is unsupported")
        revision_date = row.get("revision_date")
        if revision_date is not None:
            if not isinstance(revision_date, str):
                raise ValueError(f"{path_label}.revision_date must be ISO date")
            try:
                date.fromisoformat(revision_date)
            except ValueError as exc:
                raise ValueError(
                    f"{path_label}.revision_date must be ISO date"
                ) from exc
        sources.append(
            PKSource(
                id=source_id,
                title=_required_text(row, "title", path_label),
                url=url,
                evidence_type=evidence_type,
                revision_date=revision_date,
            )
        )
        source_ids.add(source_id)

    observations: list[PKObservation] = []
    observation_ids: set[str] = set()
    for index, row in enumerate(raw["observations"]):
        path_label = f"observations[{index}]"
        if not isinstance(row, dict):
            raise ValueError(f"{path_label} must be an object")
        observation_id = _required_text(row, "id", path_label)
        if observation_id in observation_ids:
            raise ValueError(f"Duplicate PK observation: {observation_id}")
        drug_id = _required_text(row, "drug_id", path_label)
        route = _required_text(row, "route", path_label)
        release_type = _required_text(row, "release_type", path_label)
        if route not in ROUTE_OPTIONS or release_type not in RELEASE_TYPE_OPTIONS:
            raise ValueError(f"{path_label} has unknown formulation values")
        if (drug_id, route, release_type) not in formulations:
            raise ValueError(f"{path_label} must match a curated formulation")
        metric = _required_text(row, "metric", path_label)
        unit = _required_text(row, "unit", path_label)
        if metric not in METRIC_UNITS or unit != METRIC_UNITS[metric]:
            raise ValueError(f"{path_label} has unsupported metric or unit")
        min_value = _number(row, "min_value", path_label)
        max_value = _number(row, "max_value", path_label)
        if min_value > max_value or (metric == "bioavailability" and max_value > 1):
            raise ValueError(f"{path_label} has an invalid measurement range")
        source_id = _required_text(row, "source_id", path_label)
        if source_id not in source_ids:
            raise ValueError(f"{path_label} references an unknown source")
        dose_value = row.get("dose_value")
        dose_unit = row.get("dose_unit")
        if (dose_value is None) != (dose_unit is None):
            raise ValueError(f"{path_label} requires both dose fields")
        if metric in {"cmax", "auc"} and dose_value is None:
            raise ValueError(f"{path_label} requires a measured dose")
        if dose_value is not None:
            dose_value = _number(row, "dose_value", path_label)
            if dose_value == 0:
                raise ValueError(f"{path_label}.dose_value must be positive")
            dose_unit = _required_text(row, "dose_unit", path_label)
        notes = row.get("notes")
        if notes is not None and not isinstance(notes, str):
            raise ValueError(f"{path_label}.notes must be text")
        math_eligible = row.get("math_eligible", False)
        if not isinstance(math_eligible, bool):
            raise ValueError(f"{path_label}.math_eligible must be boolean")
        if math_eligible and (
            metric != "half_life" or min_value <= 0 or min_value != max_value
        ):
            raise ValueError(
                f"{path_label}.math_eligible requires a single positive half-life"
            )
        observations.append(
            PKObservation(
                id=observation_id,
                drug_id=drug_id,
                route=route,
                release_type=release_type,
                metric=cast(PKMetric, metric),
                min_value=min_value,
                max_value=max_value,
                unit=unit,
                population=_required_text(row, "population", path_label),
                analyte=_required_text(row, "analyte", path_label),
                administration_condition=_required_text(
                    row, "administration_condition", path_label
                ),
                source_id=source_id,
                dose_value=dose_value,
                dose_unit=dose_unit,
                notes=notes,
                math_eligible=math_eligible,
            )
        )
        observation_ids.add(observation_id)
    return tuple(sources), tuple(observations)
