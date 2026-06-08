import { createMockReading } from "./mockApi";
import type { CreateReadingInput, ReadingResult } from "../types";

function getApiBaseUrl(): string {
  return import.meta.env.VITE_API_BASE_URL?.trim() ?? "";
}

function shouldUseMockMode(): boolean {
  const appMode = import.meta.env.VITE_APP_MODE?.trim().toLowerCase();
  return appMode === "mock" || !getApiBaseUrl();
}

export async function createReading(input: CreateReadingInput): Promise<ReadingResult> {
  if (shouldUseMockMode()) {
    return createMockReading(input);
  }

  const response = await fetch(`${getApiBaseUrl()}/api/readings/create`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      spread: input.spread,
      question: input.question,
      initData: input.initData,
    }),
  });

  if (!response.ok) {
    throw new Error(`Reading API failed with status ${response.status}`);
  }

  return response.json() as Promise<ReadingResult>;
}
