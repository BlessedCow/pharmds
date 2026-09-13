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

export type DrugCatalogEntry = {
  id: string;
  generic_name: string;
  drug_class: string | null;
  aliases: string[];
  release_types: string[];
  formulations: DrugFormulation[];
};

export type DrugCatalogResponse = {
  drugs: DrugCatalogEntry[];
};

export type AnalyzeDrugInput = {
  name: string;
  route?: string | null;
  release_type?: string | null;
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
