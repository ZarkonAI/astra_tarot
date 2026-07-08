export type SpreadSlug = "daily_card" | "quick" | "love" | "money" | "deep";

export type SpreadType = "daily" | "full";

export interface SpreadConfig {
  slug: SpreadSlug;
  title: string;
  shortTitle: string;
  cardsCount: number;
  type: SpreadType;
  priceLabel: string;
  description: string;
  bestFor: string;
  icon: string;
  coverImage?: string;
}

export interface ArcanaCard {
  number: number;
  slug: string;
  title: string;
  shortMeaning: string;
  image?: string;
}

export interface ReadingCard {
  position: string;
  title: string;
  meaning: string;
  slug?: string;
  symbol?: string;
  archetype?: string;
  light?: string;
  shadow?: string;
  image?: string;
}

export interface ReadingResult {
  id?: string;
  spread: SpreadSlug;
  spreadTitle: string;
  question: string;
  cards: ReadingCard[];
  interpretation: string;
  guideAdvice: string;
  disclaimer: string;
  createdAt: string;
}

export type AppScreen = "welcome" | "home" | "spread" | "ritual" | "result";

export interface CreateReadingInput {
  spread: SpreadSlug;
  question: string;
  initData: string;
  telegramUser?: TelegramUser | null;
}

export interface TelegramUser {
  id?: number;
  first_name?: string;
  last_name?: string;
  username?: string;
  language_code?: string;
}

