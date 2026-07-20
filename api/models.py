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


class AnalyzeInputPayload(BaseModel):
    drug_names: list[str]
    selected_domains: list[str]
    patient_flags: dict[str, bool]


class AnalyzePayload(BaseModel):
    schema_version: str
    input: AnalyzeInputPayload
    pairs: list[dict[str, Any]]
    regimen_summary: dict[str, Any] | None = None
    mechanism_pipeline: dict[str, Any] | None = None
    public_result_summaries: list[dict[str, Any]] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    ok: bool
    payload: AnalyzePayload
    

class MetadataResponse(BaseModel):
    domains: list[str]
    patient_flags: list[str]
    routes: list[str]
    release_types: list[str]