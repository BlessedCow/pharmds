from __future__ import annotations

import math

from fastapi import APIRouter, HTTPException, Query, status

from api.models import (
    DrugCatalogEntryResponse,
    DrugCatalogResponse,
    DrugDosageOptionResponse,
    DrugFormulationResponse,
    PKCalculationTraceResponse,
    PKObservationMathResponse,
    PKObservationResponse,
    PKObservationsResponse,
    PKSourceResponse,
)
from app.cli import DB_PATH, connect
from core.pk_math.first_order import fraction_remaining, fraction_to_steady_state
from core.pk_observations.models import PKObservation, PKSource
from core.pk_observations.store import get_pk_observations
from data.drug_catalog import (
    DrugCatalogEntry,
    get_drug_catalog_entry,
    list_drug_catalog,
)

router = APIRouter(prefix="/drugs", tags=["drugs"])


def _serialize_observation(
    observation: PKObservation, source: PKSource
) -> PKObservationResponse:
    return PKObservationResponse(
        id=observation.id,
        drug_id=observation.drug_id,
        route=observation.route,
        release_type=observation.release_type,
        metric=observation.metric,
        min_value=observation.min_value,
        max_value=observation.max_value,
        unit=observation.unit,
        population=observation.population,
        analyte=observation.analyte,
        administration_condition=observation.administration_condition,
        dose_value=observation.dose_value,
        dose_unit=observation.dose_unit,
        notes=observation.notes,
        math_eligible=observation.math_eligible,
        source=PKSourceResponse(**vars(source)),
    )


def _observations_for_drug(
    drug_id: str, *, route: str | None = None, release_type: str | None = None
) -> tuple[tuple[PKObservation, PKSource], ...]:
    with connect(DB_PATH) as conn:
        if get_drug_catalog_entry(conn, drug_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "unknown_drug", "drug_id": drug_id},
            )
        return get_pk_observations(
            conn, drug_id, route=route, release_type=release_type
        )


@router.get("/{drug_id}/pk-observations", response_model=PKObservationsResponse)
def get_drug_pk_observations(
    drug_id: str, route: str | None = None, release_type: str | None = None
) -> PKObservationsResponse:
    normalized = drug_id.strip().lower()
    observations = _observations_for_drug(
        normalized, route=route, release_type=release_type
    )
    return PKObservationsResponse(
        drug_id=normalized,
        observations=[_serialize_observation(o, s) for o, s in observations],
    )


@router.get(
    "/{drug_id}/pk-observations/{observation_id}/math",
    response_model=PKObservationMathResponse,
)
def get_drug_pk_observation_math(
    drug_id: str,
    observation_id: str,
    elapsed_hours: float = Query(ge=0, le=100_000),
) -> PKObservationMathResponse:
    normalized = drug_id.strip().lower()
    matches = _observations_for_drug(normalized)
    selected = next(((o, s) for o, s in matches if o.id == observation_id), None)
    if selected is None:
        raise HTTPException(status_code=404, detail="Unknown PK observation for drug")
    observation, source = selected
    if not math.isfinite(elapsed_hours) or not 0 <= elapsed_hours <= 100_000:
        raise HTTPException(
            status_code=422, detail="Elapsed hours must be between 0 and 100000"
        )
    if (
        not observation.math_eligible
        or observation.metric != "half_life"
        or observation.unit != "hours"
        or observation.min_value <= 0
        or observation.min_value != observation.max_value
    ):
        raise HTTPException(
            status_code=422,
            detail="Math requires a single positive sourced half-life in hours",
        )
    traces = (
        fraction_remaining(
            observation.min_value, elapsed_hours, source_ids=(source.id,)
        ),
        fraction_to_steady_state(
            observation.min_value, elapsed_hours, source_ids=(source.id,)
        ),
    )
    return PKObservationMathResponse(
        observation=_serialize_observation(observation, source),
        elapsed_hours=elapsed_hours,
        traces=[
            PKCalculationTraceResponse(
                **{
                    **vars(trace),
                    "inputs": [vars(value) for value in trace.inputs],
                }
            )
            for trace in traces
        ],
    )


def _serialize_drug(
    entry: DrugCatalogEntry,
) -> DrugCatalogEntryResponse:
    return DrugCatalogEntryResponse(
        id=entry.id,
        generic_name=entry.generic_name,
        drug_class=entry.drug_class,
        aliases=list(entry.aliases),
        release_types=list(entry.release_types),
        formulations=[
            DrugFormulationResponse(
                route=formulation.route,
                release_types=list(formulation.release_types),
            )
            for formulation in entry.formulations
        ],
        dosage_options=[
            DrugDosageOptionResponse(
                route=option.route,
                release_type=option.release_type,
                dosage_form=option.dosage_form,
                strength_value=option.strength_value,
                strength_unit=option.strength_unit,
                product_name=option.product_name,
                composition=option.composition,
                source_url=option.source_url,
            )
            for option in entry.dosage_options
        ],
    )


@router.get("", response_model=DrugCatalogResponse)
def get_drugs() -> DrugCatalogResponse:
    with connect(DB_PATH) as conn:
        entries = list_drug_catalog(conn)

    return DrugCatalogResponse(drugs=[_serialize_drug(entry) for entry in entries])


@router.get(
    "/{drug_id}",
    response_model=DrugCatalogEntryResponse,
)
def get_drug(
    drug_id: str,
) -> DrugCatalogEntryResponse:
    normalized_drug_id = drug_id.strip().lower()

    with connect(DB_PATH) as conn:
        entry = get_drug_catalog_entry(
            conn,
            normalized_drug_id,
        )

    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "unknown_drug",
                "drug_id": normalized_drug_id,
            },
        )

    return _serialize_drug(entry)
