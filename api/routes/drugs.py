from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from api.models import (
    DrugCatalogEntryResponse,
    DrugCatalogResponse,
    DrugDosageOptionResponse,
    DrugFormulationResponse,
)
from app.cli import DB_PATH, connect
from data.drug_catalog import (
    DrugCatalogEntry,
    get_drug_catalog_entry,
    list_drug_catalog,
)

router = APIRouter(prefix="/drugs", tags=["drugs"])


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
