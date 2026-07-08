import { createMockReading } from "./mockApi";
import { getTelegramUser } from "./telegram";
import type { CreateReadingInput, ReadingCard, ReadingResult, SpreadSlug } from "../types";

const API_STORAGE_KEY = "astra_api_base_url";
const FRIENDLY_READING_ERROR = "\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u043f\u043e\u043b\u0443\u0447\u0438\u0442\u044c \u0440\u0430\u0441\u043a\u043b\u0430\u0434. \u041f\u043e\u043f\u0440\u043e\u0431\u0443\u0439\u0442\u0435 \u0435\u0449\u0435 \u0440\u0430\u0437.";

type ApiStatus = "mock" | "connected" | "error";

type ApiReadingCard = Partial<ReadingCard> & {
  light?: string;
  shadow?: string;
};

type ApiReadingSuccess = Partial<ReadingResult> & {
  ok?: true;
  source?: "openrouter" | "local" | "fallback";
  spread: SpreadSlug;
  spreadTitle: string;
  cards: ApiReadingCard[];
  interpretation: string;
};

type ApiReadingFailure = {
  ok: false;
  error?: string;
  message?: string;
};

type ApiReadingResponse = ApiReadingSuccess | ApiReadingFailure;

class UserVisibleApiError extends Error {}

let apiStatus: ApiStatus = "mock";

function normalizeApiBaseUrl(value: string | null | undefined): string | null {
  const trimmed = String(value || "").trim();
  if (!trimmed) {
    return null;
  }
  return trimmed.replace(/\/+$/, "");
}

function readQueryApiBaseUrl(): string | null | undefined {
  const params = new URLSearchParams(window.location.search);
  if (!params.has("api")) {
    return undefined;
  }

  const rawValue = params.get("api") || "";
  if (rawValue.trim().toLowerCase() === "clear") {
    window.localStorage.removeItem(API_STORAGE_KEY);
    return null;
  }

  const apiBaseUrl = normalizeApiBaseUrl(rawValue);
  if (apiBaseUrl) {
    window.localStorage.setItem(API_STORAGE_KEY, apiBaseUrl);
  }
  return apiBaseUrl;
}

export function getApiBaseUrl(): string | null {
  const queryApiBaseUrl = readQueryApiBaseUrl();
  if (queryApiBaseUrl !== undefined) {
    return queryApiBaseUrl;
  }

  const storageApiBaseUrl = normalizeApiBaseUrl(window.localStorage.getItem(API_STORAGE_KEY));
  if (storageApiBaseUrl) {
    return storageApiBaseUrl;
  }

  return normalizeApiBaseUrl(import.meta.env.VITE_API_BASE_URL);
}

export function getApiStatus(): ApiStatus {
  return apiStatus;
}

export function shouldShowApiDebug(): boolean {
  const params = new URLSearchParams(window.location.search);
  return params.get("debug") === "1" || import.meta.env.DEV;
}

export function getApiDebugLabel(): string {
  return `API: ${apiStatus}`;
}

function toReadingCard(card: ApiReadingCard): ReadingCard {
  return {
    position: String(card.position || ""),
    title: String(card.title || ""),
    meaning: String(card.meaning || card.light || card.archetype || ""),
    slug: card.slug,
    symbol: card.symbol,
    archetype: card.archetype,
    light: card.light,
    shadow: card.shadow,
    image: card.image,
  };
}

function toReadingResult(data: ApiReadingSuccess, input: CreateReadingInput): ReadingResult {
  return {
    id: data.id,
    spread: data.spread || input.spread,
    spreadTitle: data.spreadTitle,
    question: data.question ?? input.question,
    cards: (data.cards || []).map(toReadingCard),
    interpretation: data.interpretation,
    guideAdvice: data.guideAdvice || "\u0421\u0434\u0435\u043b\u0430\u0439\u0442\u0435 \u043e\u0434\u0438\u043d \u0441\u043f\u043e\u043a\u043e\u0439\u043d\u044b\u0439 \u0448\u0430\u0433 \u0438 \u0432\u0435\u0440\u043d\u0438\u0442\u0435 \u044f\u0441\u043d\u043e\u0441\u0442\u044c.",
    disclaimer: data.disclaimer || "",
    createdAt: data.createdAt || new Date().toISOString(),
  };
}

function getFriendlyFailureMessage(data: ApiReadingFailure): string {
  if (data.error === "limit_reached" && data.message) {
    return data.message;
  }
  return data.message || FRIENDLY_READING_ERROR;
}

async function createApiReading(apiBaseUrl: string, input: CreateReadingInput): Promise<ReadingResult> {
  const response = await fetch(`${apiBaseUrl}/api/readings/create`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      spread: input.spread,
      question: input.question,
      initData: input.initData,
      telegramUser: input.telegramUser ?? getTelegramUser() ?? null,
    }),
  });

  if (!response.ok) {
    throw new Error(FRIENDLY_READING_ERROR);
  }

  const data = (await response.json()) as ApiReadingResponse;
  if (data.ok === false) {
    if (data.error === "limit_reached") {
      throw new UserVisibleApiError(getFriendlyFailureMessage(data));
    }
    throw new Error(FRIENDLY_READING_ERROR);
  }

  if (!data.cards?.length || !data.interpretation) {
    throw new Error(FRIENDLY_READING_ERROR);
  }

  apiStatus = "connected";
  return toReadingResult(data, input);
}

export async function createReading(input: CreateReadingInput): Promise<ReadingResult> {
  const apiBaseUrl = getApiBaseUrl();
  if (!apiBaseUrl) {
    apiStatus = "mock";
    return createMockReading(input);
  }

  try {
    return await createApiReading(apiBaseUrl, input);
  } catch (error) {
    if (error instanceof UserVisibleApiError) {
      throw error;
    }
    apiStatus = "error";
    return createMockReading(input);
  }
}


