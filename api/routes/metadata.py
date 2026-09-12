from __future__ import annotations

from fastapi import APIRouter

from api.models import MetadataResponse
from core.formulations import (
    RELEASE_TYPE_OPTIONS,
    ROUTE_OPTIONS,
)

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
    )