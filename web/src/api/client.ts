import type { MetadataResponse } from "./types";

export async function fetchMetadata(): Promise<MetadataResponse> {
  const response = await fetch("/api/metadata");

  if (!response.ok) {
    throw new Error("Failed to load PharmDS metadata.");
  }

  return response.json() as Promise<MetadataResponse>;
}