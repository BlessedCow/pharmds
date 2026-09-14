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

    strength_value: float | None = Field(
        default=None,
        gt=0,
        description="Optional selected curated strength value.",
    )
    strength_unit: str | None = Field(
        default=None,
        description="Unit for the selected curated strength.",
    )
    dosage_form: str | None = Field(
        default=None,
        description="Dosage form for the selected curated strength.",
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
    pd_effects: list[str] | None = Field(
        default=None,
        description=(
            "Optional canonical PD effect IDs to include. "
            "Null means include all supported PD effects."
        ),
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
    drug_inputs: list[dict[str, Any]] = Field(default_factory=list)

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
    pd_effects: list[str] | None = Field(
        default=None,
        description=(
            "Optional canonical PD effect IDs to include. "
            "Null means include all supported PD effects."
        ),
    )


class PdEffectOptionResponse(BaseModel):
    id: str
    label: str


class MetadataResponse(BaseModel):
    domains: list[str]
    patient_flags: list[str]
    routes: list[str]
    release_types: list[str]
    pd_effects: list[PdEffectOptionResponse]


class DrugFormulationResponse(BaseModel):
    route: str
    release_types: list[str]


class DrugDosageOptionResponse(BaseModel):
    route: str
    release_type: str
    dosage_form: str
    strength_value: float
    strength_unit: str


class DrugCatalogEntryResponse(BaseModel):
    id: str
    generic_name: str
    drug_class: str | None
    aliases: list[str]
    release_types: list[str]
    formulations: list[DrugFormulationResponse]
    dosage_options: list[DrugDosageOptionResponse]


class DrugCatalogResponse(BaseModel):
    drugs: list[DrugCatalogEntryResponse]