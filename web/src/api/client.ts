import type {
  AnalyzeRequest,
  AnalyzeResponse,
  ApiErrorResponse,
  DrugCatalogEntry,
  DrugCatalogResponse,
  MetadataResponse,
  KnowledgeQueryResponse,
  KnowledgeStatusResponse,
} from "./types";

export async function fetchMetadata(): Promise<MetadataResponse> {
  const response = await fetch("/api/metadata");

  if (!response.ok) {
    throw new Error("Failed to load PharmDS metadata.");
  }

  return response.json() as Promise<MetadataResponse>;
}

export async function fetchDrugCatalog(): Promise<DrugCatalogResponse> {
  const response = await fetch("/api/drugs");

  if (!response.ok) {
    throw new Error("Failed to load PharmDS drug catalog.");
  }

  return response.json() as Promise<DrugCatalogResponse>;
}

export async function fetchDrug(
  drugId: string,
): Promise<DrugCatalogEntry> {
  const response = await fetch(
    `/api/drugs/${encodeURIComponent(drugId)}`,
  );

  if (!response.ok) {
    const errorBody = (await response
      .json()
      .catch(() => null)) as ApiErrorResponse | null;

    throw new Error(formatApiError(errorBody));
  }

  return response.json() as Promise<DrugCatalogEntry>;
}

export async function analyzeDrugs(
  request: AnalyzeRequest,
): Promise<AnalyzeResponse> {
  const response = await fetch("/api/analyze", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorBody = (await response
      .json()
      .catch(() => null)) as ApiErrorResponse | null;

    throw new Error(formatApiError(errorBody));
  }

  return response.json() as Promise<AnalyzeResponse>;
}

export async function fetchKnowledgeStatus(): Promise<KnowledgeStatusResponse> {
  const response = await fetch("/api/knowledge/status");
  if (!response.ok) {
    throw new Error("Failed to load knowledge service status.");
  }
  return response.json() as Promise<KnowledgeStatusResponse>;
}

export async function queryKnowledge(
  query: string,
  topK = 5,
): Promise<KnowledgeQueryResponse> {
  const response = await fetch("/api/knowledge/query", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({query, top_k: topK}),
  });
  if (!response.ok) {
    const errorBody = (await response.json().catch(() => null)) as
      | ApiErrorResponse
      | null;
    throw new Error(formatApiError(errorBody));
  }
  return response.json() as Promise<KnowledgeQueryResponse>;
}

function formatApiError(errorBody: ApiErrorResponse | null): string {
  if (errorBody?.detail && typeof errorBody.detail === "object") {
    const detail = errorBody.detail as Record<string, unknown>;

    if (typeof detail.message === "string") {
      return detail.message;
    }

    if (typeof detail.error === "string") {
      return detail.error;
    }
  }

  if (typeof errorBody?.detail === "string") {
    return errorBody.detail;
  }

  return "Failed to complete the PharmDS API request.";
}