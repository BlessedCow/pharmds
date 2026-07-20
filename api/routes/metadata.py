from __future__ import annotations

from fastapi import APIRouter

from api.models import MetadataResponse

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

ROUTE_OPTIONS = [
    "oral",
    "iv",
    "im",
    "sc",
    "transdermal",
    "inhaled",
    "intranasal",
    "sublingual",
    "rectal",
    "topical",
    "ophthalmic",
    "otic",
    "unknown",
]

RELEASE_TYPE_OPTIONS = [
    "ir",
    "sr",
    "er",
    "xr",
    "dr",
    "la",
    "depot",
    "unknown",
]


@router.get("/metadata", response_model=MetadataResponse)
def get_metadata() -> MetadataResponse:
    return MetadataResponse(
        domains=DOMAIN_OPTIONS,
        patient_flags=PATIENT_FLAG_OPTIONS,
        routes=ROUTE_OPTIONS,
        release_types=RELEASE_TYPE_OPTIONS,
    )
