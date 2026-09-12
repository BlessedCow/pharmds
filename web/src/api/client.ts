import type {
  AnalyzeRequest,
  AnalyzeResponse,
  ApiErrorResponse,
  MetadataResponse,
} from "./types";

export async function fetchMetadata(): Promise<MetadataResponse> {
  const response = await fetch("/api/metadata");

  if (!response.ok) {
    throw new Error("Failed to load PharmDS metadata.");
  }

  return response.json() as Promise<MetadataResponse>;
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

  return "Failed to analyze medications.";
}
