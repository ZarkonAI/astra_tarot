import type { ReadingResult, SpreadConfig } from "../types";

export function buildMockReading(spread: SpreadConfig, question: string): Omit<ReadingResult, "cards"> {
  const normalizedQuestion = question.trim();

  return {
    id: `mock-${Date.now()}`,
    spread: spread.slug,
    spreadTitle: spread.title,
    question: normalizedQuestion,
    interpretation: normalizedQuestion
      ? "Я смотрю на ваш вопрос как на пространство для спокойного выбора. Карты предлагают не торопиться с выводами: сначала отделить факты от тревожных ожиданий, затем выбрать один маленький шаг, который вернет ощущение опоры."
      : "Сегодня расклад говорит о мягком возвращении к себе. Не обязательно искать большой знак: иногда достаточно заметить, где становится легче дышать, и дать этому направлению немного больше внимания.",
    guideAdvice:
      "Мой совет: прислушайтесь к первому спокойному ощущению, но оставьте себе право уточнять решение. Символы помогают размышлять, а окончательный выбор остается за вами.",
    disclaimer:
      "Расклад носит развлекательный и рефлексивный характер и не заменяет помощь специалиста.",
    createdAt: new Date().toISOString(),
  };
}
