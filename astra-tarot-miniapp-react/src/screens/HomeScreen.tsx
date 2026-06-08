import { ArcanaPreview } from "../components/ArcanaPreview";
import { SafetyNote } from "../components/SafetyNote";
import { SpreadCard } from "../components/SpreadCard";
import { spreads } from "../data/spreads";
import type { SpreadConfig } from "../types";

interface HomeScreenProps {
  firstName?: string;
  onSelectSpread: (spread: SpreadConfig) => void;
}

export function HomeScreen({ firstName, onSelectSpread }: HomeScreenProps) {
  const dailySpread = spreads.find((spread) => spread.slug === "daily_card");
  const paidSpreads = spreads.filter((spread) => spread.slug !== "daily_card");

  return (
    <section className="screen home-screen screen-enter">
      <header className="home-header">
        <p className="eyebrow">Astra Tarot</p>
        <h1>{firstName ? `Здравствуйте, ${firstName}` : "Добро пожаловать"}</h1>
        <p>Сегодня можно начать с карты дня или выбрать расклад глубже.</p>
      </header>

      {dailySpread && (
        <section className="daily-section">
          <SpreadCard spread={dailySpread} isFeatured onSelect={onSelectSpread} />
        </section>
      )}

      <section className="spreads-section">
        <div className="section-heading">
          <p className="eyebrow">Выбор расклада</p>
          <h2>Выберите формат</h2>
        </div>
        <div className="spread-grid">
          {paidSpreads.map((spread) => (
            <SpreadCard key={spread.slug} spread={spread} onSelect={onSelectSpread} />
          ))}
        </div>
      </section>

      <ArcanaPreview />
      <SafetyNote />
    </section>
  );
}
