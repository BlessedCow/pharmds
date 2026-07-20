from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    drug_names: list[str] = Field(
        min_length=2,
        description="Drug names, generic names, or supported aliases to analyze.",
    )
    domain: str = Field(
        default="all",
        description="Interaction domain filter. Use 'all' unless narrowing analysis.",
    )
    qt_risk: bool = Field(
        default=False,
        description="Whether to include patient-specific QT risk context.",
    )
    bleeding_risk: bool = Field(
        default=False,
        description="Whether to include patient-specific bleeding risk context.",
    )


class AnalyzeResponse(BaseModel):
    ok: bool
    payload: dict[str, Any]