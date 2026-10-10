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
    dose_value: float | None = Field(
        default=None,
        gt=0,
        description="Optional dose per administration for this regimen.",
    )
    dose_unit: str | None = Field(
        default=None,
        description="Unit for the regimen dose per administration.",
    )
    frequency: str | None = Field(
        default=None,
        description=(
            "Optional regimen frequency. Recognized timing semantics include "
            "daypart codes (QAM/QPM/QHS), daily-count codes (QD/BID/TID/QID), "
            "fixed intervals such as Q4H/Q8H, weekly/calendar schedules, and "
            "meal-relative codes. Unrecognized values are preserved as custom."
        ),
    )
    schedule_type: str | None = Field(
        default=None,
        pattern="^(scheduled|prn)$",
        description="Whether the regimen is scheduled or PRN.",
    )
    administrations_per_day: float | None = Field(
        default=None,
        gt=0,
        description="Optional explicit scheduled administrations per day.",
    )
    max_administrations_per_day: float | None = Field(
        default=None,
        gt=0,
        description="Optional maximum administrations per day for PRN use.",
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
    product_name: str | None = None
    composition: str | None = None
    source_url: str | None = None


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


class PKSourceResponse(BaseModel):
    id: str
    title: str
    url: str
    evidence_type: str
    revision_date: str | None


class PKObservationResponse(BaseModel):
    id: str
    drug_id: str
    route: str
    release_type: str
    metric: str
    min_value: float
    max_value: float
    unit: str
    population: str
    analyte: str
    administration_condition: str
    dose_value: float | None
    dose_unit: str | None
    notes: str | None
    math_eligible: bool
    source: PKSourceResponse


class PKObservationsResponse(BaseModel):
    drug_id: str
    observations: list[PKObservationResponse]


class PKCalculationInputResponse(BaseModel):
    name: str
    value: float
    unit: str


class PKCalculationTraceResponse(BaseModel):
    calculation: str
    formula: str
    substitutions: str
    inputs: list[PKCalculationInputResponse]
    elimination_rate_per_hour: float
    result: float
    result_unit: str
    assumptions: list[str]
    limitations: list[str]
    source_ids: list[str]


class PKObservationMathResponse(BaseModel):
    observation: PKObservationResponse
    elapsed_hours: float
    traces: list[PKCalculationTraceResponse]

