from __future__ import annotations

from fastapi import APIRouter

from api.models import AnalyzeRequest, AnalyzeResponse
from app.service import analyze_names

router = APIRouter(prefix="/analyze", tags=["analyze"])


@router.post("", response_model=AnalyzeResponse)
def analyze_drugs(request: AnalyzeRequest) -> AnalyzeResponse:
    result = analyze_names(
        request.drug_names,
        domain=request.domain,
        qt_risk=request.qt_risk,
        bleeding_risk=request.bleeding_risk,
        as_json_payload=True,
    )

    return AnalyzeResponse(
        ok=result.ok,
        payload=result.payload,
    )