from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AnalyzeDrugInput(BaseModel):
    name: str = Field(
        min_length=1,
        description="Drug name, generic name, or supported alias to analyze.",
    )
    route: str | None = Field(
        default=None,
        description="Optional route for this drug's PK timing lookup.",
    )
    release_type: str | None = Field(
        default=None,
        description="Optional release type for this drug's PK timing lookup.",
    )


class AnalyzeRequest(BaseModel):
    drug_names: list[str] | None = Field(
        default=None,
        description="Drug names, generic names, or supported aliases to analyze.",
    )
    drugs: list[AnalyzeDrugInput] | None = Field(
        default=None,
        description="Structured drug inputs for route- and release-aware analysis.",
    )
    domain: str = Field(
        default="all",
        description="Interaction domain filter. Use 'all' unless narrowing analysis.",
    )
    route: str | None = Field(
        default=None,
        description=(
            "Optional regimen-level route used for pharmacokinetic timing lookup."
        ),
    )
    release_type: str | None = Field(
        default=None,
        description=(
            "Optional regimen-level release type used "
            "for pharmacokinetic timing lookup."
        ),
    )
    qt_risk: bool = Field(
        default=False,
        description="Whether to include patient-specific QT risk context.",
    )
    bleeding_risk: bool = Field(
        default=False,
        description="Whether to include patient-specific bleeding risk context.",
    )


class AnalyzePkTimingInputPayload(BaseModel):
    route: str
    release_type: str
    route_source: str
    release_type_source: str


class AnalyzeInputPayload(BaseModel):
    drug_names: list[str]
    selected_domains: list[str]
    patient_flags: dict[str, bool]
    pk_timing: AnalyzePkTimingInputPayload
    pk_timing_by_drug: list[dict[str, Any]] = Field(default_factory=list)

class AnalyzePayload(BaseModel):
    schema_version: str
    input: AnalyzeInputPayload
    pairs: list[dict[str, Any]]
    pk_timing_context: list[dict[str, Any]] = Field(default_factory=list)
    pk_timing_interpretation: list[dict[str, Any]] = Field(default_factory=list)
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
