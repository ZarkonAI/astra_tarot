interface SafetyNoteProps {
  variant?: "default" | "love" | "money";
}

const notes = {
  default: "Выберите один образ, который хочется взять с собой дальше.",
  love: "Мягкий вопрос к себе иногда говорит больше, чем быстрый вывод.",
  money: "Спокойный шаг начинается с ясного взгляда на то, что уже есть.",
};

export function SafetyNote({ variant = "default" }: SafetyNoteProps) {
  return <p className="safety-note">{notes[variant]}</p>;
}
