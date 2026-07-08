import { BottomAction } from "../components/BottomAction";
import { RitualLoader } from "../components/RitualLoader";
import type { SpreadConfig } from "../types";

interface RitualScreenProps {
  spread: SpreadConfig;
  error?: string;
  onBack: () => void;
}

function getRitualTitle(spread: SpreadConfig): string {
  const titles: Record<string, string> = {
    daily_card: "Звезда выбирает карту дня...",
    quick: "Звезда перемешивает карты для быстрого ответа...",
    love: "Звезда мягко раскрывает сердечный расклад...",
    money: "Звезда собирает знаки денежного пути...",
    deep: "Звезда раскладывает карты и собирает нити смысла...",
  };
  return titles[spread.slug] ?? "Звезда выбирает карты...";
}

export function RitualScreen({ spread, error, onBack }: RitualScreenProps) {
  return (
    <section className="screen ritual-screen screen-enter">
      <RitualLoader title={getRitualTitle(spread)} />
      {error && (
        <>
          <div className="error-box" role="alert">
            {error}
          </div>
          <BottomAction primaryLabel="Вернуться" onPrimary={onBack} />
        </>
      )}
    </section>
  );
}
