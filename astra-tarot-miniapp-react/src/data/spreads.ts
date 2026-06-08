import type { SpreadConfig, SpreadSlug } from "../types";

export const spreads: SpreadConfig[] = [
  {
    slug: "daily_card",
    title: "Карта дня",
    shortTitle: "Карта дня",
    cardsCount: 1,
    type: "daily",
    priceLabel: "Бесплатно 1 раз в сутки",
    description: "Короткий символический совет на сегодня.",
    bestFor: "Когда хочется мягко понять настроение дня.",
    icon: "✦",
    coverImage: "/assets/covers/cover_daily.webp",
  },
  {
    slug: "quick",
    title: "Быстрый расклад",
    shortTitle: "Быстрый",
    cardsCount: 1,
    type: "full",
    priceLabel: "Первый расклад бесплатно",
    description: "Короткий ответ, когда нужно понять общий вектор ситуации.",
    bestFor: "Для простого вопроса без лишних деталей.",
    icon: "☽",
    coverImage: "/assets/covers/cover_quick.webp",
  },
  {
    slug: "love",
    title: "Сердечный расклад",
    shortTitle: "Сердечный",
    cardsCount: 3,
    type: "full",
    priceLabel: "Расклад на отношения",
    description: "Бережный взгляд на чувства, контакт и личные границы.",
    bestFor: "Когда важно разобраться в отношениях без давления и ожиданий.",
    icon: "♡",
    coverImage: "/assets/covers/cover_love.webp",
  },
  {
    slug: "money",
    title: "Денежный путь",
    shortTitle: "Деньги",
    cardsCount: 3,
    type: "full",
    priceLabel: "Символический финансовый фокус",
    description: "Расклад о ресурсах, привычках и спокойных следующих шагах.",
    bestFor: "Когда хочется посмотреть на деньги как на тему выбора и опоры.",
    icon: "₽",
    coverImage: "/assets/covers/cover_money.webp",
  },
  {
    slug: "deep",
    title: "Глубокий расклад",
    shortTitle: "Глубокий",
    cardsCount: 5,
    type: "full",
    priceLabel: "Подробный символический разбор",
    description: "Несколько карт помогают увидеть слои ситуации и возможный фокус.",
    bestFor: "Для сложных тем, где нужен спокойный обзор без поспешных выводов.",
    icon: "✺",
    coverImage: "/assets/covers/cover_deep.webp",
  },
];

export const spreadBySlug = new Map<SpreadSlug, SpreadConfig>(
  spreads.map((spread) => [spread.slug, spread]),
);

export function getSpread(slug: SpreadSlug): SpreadConfig {
  const spread = spreadBySlug.get(slug);
  if (!spread) {
    throw new Error(`Unknown spread: ${slug}`);
  }

  return spread;
}
