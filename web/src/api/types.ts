export type PdEffectOption = {
  id: string;
  label: string;
};

export type MetadataResponse = {
  domains: string[];
  patient_flags: string[];
  routes: string[];
  release_types: string[];
  pd_effects: PdEffectOption[];
};

export type DrugFormulation = {
  route: string;
  release_types: string[];
};

export type DrugDosageOption = {
  route: string;
  release_type: string;
  dosage_form: string;
  strength_value: number;
  strength_unit: string;
  product_name: string | null;
  composition: string | null;
  source_url: string | null;
};

export type DrugCatalogEntry = {
  id: string;
  generic_name: string;
  drug_class: string | null;
  aliases: string[];
  release_types: string[];
  formulations: DrugFormulation[];
  dosage_options: DrugDosageOption[];
};

export type DrugCatalogResponse = {
  drugs: DrugCatalogEntry[];
};

export type PKObservation = {
  id: string;
  drug_id: string;
  route: string;
  release_type: string;
  metric: string;
  min_value: number;
  max_value: number;
  unit: string;
  population: string;
  analyte: string;
  administration_condition: string;
  dose_value: number | null;
  dose_unit: string | null;
  notes: string | null;
  math_eligible: boolean;
  source: {
    id: string;
    title: string;
    url: string;
    evidence_type: string;
    revision_date: string | null;
  };
};

export type PKObservationsResponse = {
  drug_id: string;
  observations: PKObservation[];
};

export type PKCalculationTrace = {
  calculation: string;
  formula: string;
  substitutions: string;
  inputs: Array<{ name: string; value: number; unit: string }>;
  elimination_rate_per_hour: number;
  result: number;
  result_unit: string;
  assumptions: string[];
  limitations: string[];
  source_ids: string[];
};

export type PKObservationMathResponse = {
  observation: PKObservation;
  elapsed_hours: number;
  traces: PKCalculationTrace[];
};

export type AnalyzeDrugInput = {
  name: string;
  route?: string | null;
  release_type?: string | null;
  strength_value?: number | null;
  strength_unit?: string | null;
  dosage_form?: string | null;
  dose_value?: number | null;
  dose_unit?: string | null;
  frequency?: string | null;
  schedule_type?: "scheduled" | "prn" | null;
  administrations_per_day?: number | null;
  max_administrations_per_day?: number | null;
};

export type AnalyzeRequest = {
  drugs: AnalyzeDrugInput[];
  domain?: string;
  qt_risk?: boolean;
  bleeding_risk?: boolean;
  pd_effects?: string[] | null;
};

export type DrugReference = {
  id: string;
  name: string;
};

export type RuleReference = {
  source: string;
  citation: string;
};

export type RuleHit = {
  rule_id: string;
  name: string;
  domain: string;
  severity: string;
  class: string;
  severity_rationale?: string | null;
  action_rationale?: string | null;
  inputs: Record<string, unknown>;
  tags: string[];
  explanation?: string | null;
  rationale: string[];
  actions: string[];
  references: RuleReference[];
  A?: DrugReference;
  B?: DrugReference;
};

export type PairDomainFindings = {
  summary?: string | null;
  hits: RuleHit[];
};

export type PairFinding = {
  drug_1: DrugReference;
  drug_2: DrugReference;
  overall: {
    severity: string;
    class: string;
  };
  pk: PairDomainFindings;
  pd: PairDomainFindings;
};

export type PublicResultSummary = {
  source: string;
  title: string;
  drugs: string[];
  concern_type: string;
  severity_label: string;
  evidence_label: string;
  explanation: string;
};

export type AnalyzeResponse = {
  ok: boolean;
  payload: {
    schema_version: string;
    input: {
      drug_names: string[];
      selected_domains: string[];
      patient_flags: Record<string, boolean>;
      pk_timing: {
        route: string;
        release_type: string;
        route_source: string;
        release_type_source: string;
      };
      pk_timing_by_drug: Array<Record<string, string | null>>;
      drug_inputs: Array<Record<string, unknown>>;
    };
    pairs: PairFinding[];
    pk_timing_context: Array<Record<string, unknown>>;
    pk_timing_interpretation: Array<{
      drug_id: string;
      summary: string | null;
    }>;
    regimen_summary?: Record<string, unknown> | null;
    mechanism_pipeline?: Record<string, unknown> | null;
    public_result_summaries: PublicResultSummary[];
  };
};

export type ApiErrorResponse = {
  detail?: unknown;
};


