export type MetadataResponse = {
  domains: string[];
  patient_flags: string[];
  routes: string[];
  release_types: string[];
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
    pairs: Array<Record<string, unknown>>;
    pk_timing_context: Array<Record<string, unknown>>;
    pk_timing_interpretation: Array<{
      drug_id: string;
      summary: string | null;
    }>;
    regimen_summary?: Record<string, unknown> | null;
    mechanism_pipeline?: Record<string, unknown> | null;
    public_result_summaries: Array<Record<string, unknown>>;
  };
};

export type ApiErrorResponse = {
  detail?: unknown;
};