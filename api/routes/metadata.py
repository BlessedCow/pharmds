from __future__ import annotations

from fastapi import APIRouter

from api.models import (
    MetadataResponse,
    PdEffectOptionResponse,
)
from core.formulations import (
    RELEASE_TYPE_OPTIONS,
    ROUTE_OPTIONS,
)
from core.mechanisms.effect_labels import pd_effect_options

router = APIRouter(tags=["metadata"])

DOMAIN_OPTIONS = [
    "all",
    "cyp",
    "ugt",
    "pgp",
    "transporter",
    "pd",
    "pgx",
    "named_pair",
]

PATIENT_FLAG_OPTIONS = [
    "qt_risk",
    "bleeding_risk",
]


@router.get("/metadata", response_model=MetadataResponse)
def get_metadata() -> MetadataResponse:
    return MetadataResponse(
        domains=DOMAIN_OPTIONS,
        patient_flags=PATIENT_FLAG_OPTIONS,
        routes=list(ROUTE_OPTIONS),
        release_types=list(RELEASE_TYPE_OPTIONS),
        pd_effects=[
            PdEffectOptionResponse(
                id=effect_id,
                label=label,
            )
            for effect_id, label in pd_effect_options()
        ],
    )