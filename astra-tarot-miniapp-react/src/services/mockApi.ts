import { arcana } from "../data/arcana";
import { buildMockReading } from "../data/mockReading";
import { getSpread } from "../data/spreads";
import type { CreateReadingInput, ReadingCard, ReadingResult, SpreadSlug } from "../types";

const positionsBySpread: Record<SpreadSlug, string[]> = {
  daily_card: ["Совет дня"],
  quick: ["Главный символ"],
  love: ["Что вы чувствуете", "Что важно заметить", "Бережный шаг"],
  money: ["Текущий ресурс", "Что требует внимания", "Спокойный шаг"],
  deep: ["Суть ситуации", "Скрытый фон", "Ваша опора", "Возможность", "Мягкий совет"],
};

function pickCards(count: number): ReadingCard[] {
  const shuffled = [...arcana].sort(() => Math.random() - 0.5);

  return shuffled.slice(0, count).map((card, index) => ({
    position: "",
    title: card.title,
    meaning: card.shortMeaning,
    image: card.image,
    index,
  })).map(({ index, ...card }) => card);
}

export async function createMockReading(input: CreateReadingInput): Promise<ReadingResult> {
  const spread = getSpread(input.spread);
  const delay = 1500 + Math.random() * 1000;

  await new Promise((resolve) => window.setTimeout(resolve, delay));

  const positions = positionsBySpread[spread.slug];
  const cards = pickCards(spread.cardsCount).map((card, index) => ({
    ...card,
    position: positions[index] ?? `Карта ${index + 1}`,
  }));

  return {
    ...buildMockReading(spread, input.question),
    cards,
  };
}
