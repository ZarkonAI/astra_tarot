import { AssetImage } from "../components/AssetImage";
import { BottomAction } from "../components/BottomAction";
import { QuestionBox } from "../components/QuestionBox";
import type { SpreadConfig } from "../types";

interface SpreadScreenProps {
  spread: SpreadConfig;
  question: string;
  error?: string;
  isLoading: boolean;
  onQuestionChange: (value: string) => void;
  onBack: () => void;
  onSubmit: () => void;
}

export function SpreadScreen({ spread, question, error, isLoading, onQuestionChange, onBack, onSubmit }: SpreadScreenProps) {
  return (
    <section className="screen spread-screen screen-enter">
      <button className="button button--link" type="button" onClick={onBack}>
        Назад
      </button>

      <header className="spread-hero">
        <div className="spread-hero__cover">
          <AssetImage
            className="spread-hero__image"
            path={spread.coverImage}
            fallbackPath="assets/background/card_back_ornate.webp"
            alt=""
            fallback={<span>{spread.icon}</span>}
          />
        </div>
        <p className="eyebrow">{spread.priceLabel}</p>
        <h1>{spread.title}</h1>
        <p>{spread.description}</p>
      </header>

      <div className="spread-details">
        <div>
          <span>{spread.cardsCount}</span>
          <small>карт в раскладе</small>
        </div>
        <div>
          <span>{spread.shortTitle}</span>
          <small>{spread.bestFor}</small>
        </div>
      </div>

      <QuestionBox value={question} onChange={onQuestionChange} />

      {error && (
        <div className="error-box" role="alert">
          {error}
        </div>
      )}

      <BottomAction
        primaryLabel={isLoading ? "Выбираю карты..." : "Получить расклад"}
        secondaryLabel="Назад"
        disabled={isLoading}
        onPrimary={onSubmit}
        onSecondary={onBack}
      />
    </section>
  );
}
