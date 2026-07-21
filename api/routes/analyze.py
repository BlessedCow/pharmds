from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from api.models import AnalyzeRequest, AnalyzeResponse
from app.service import analyze_names

router = APIRouter(prefix="/analyze", tags=["analyze"])


def _resolve_request_drug_names(request: AnalyzeRequest) -> list[str]:
    if request.drugs is not None:
        return [drug.name for drug in request.drugs]

    if request.drug_names is not None:
        return request.drug_names

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail="Provide either drug_names or drugs.",
    )


def _resolve_request_pk_timing_inputs(
    request: AnalyzeRequest,
) -> list[dict[str, str | None]] | None:
    if request.drugs is None:
        return None

    return [
        {
            "route": drug.route,
            "release_type": drug.release_type,
        }
        for drug in request.drugs
    ]


@router.post("", response_model=AnalyzeResponse)
def analyze_drugs(request: AnalyzeRequest) -> AnalyzeResponse:
    drug_names = _resolve_request_drug_names(request)
    pk_timing_inputs = _resolve_request_pk_timing_inputs(request)

    result = analyze_names(
        drug_names,
        domain=request.domain,
        route=request.route,
        release_type=request.release_type,
        pk_timing_inputs=pk_timing_inputs,
        qt_risk=request.qt_risk,
        bleeding_risk=request.bleeding_risk,
        as_json_payload=True,
    )

    if not result.ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.payload,
        )

    return AnalyzeResponse(
        ok=result.ok,
        payload=result.payload,
    )