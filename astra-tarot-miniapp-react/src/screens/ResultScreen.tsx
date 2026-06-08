import { AssetImage } from "../components/AssetImage";
import { StarGuide } from "../components/StarGuide";
import type { ReadingResult } from "../types";

interface ResultScreenProps {
  result: ReadingResult;
  onHome: () => void;
  onNewReading: () => void;
}

export function ResultScreen({ result, onHome, onNewReading }: ResultScreenProps) {
  return (
    <section className="screen result-screen screen-enter">
      <header className="result-header">
        <div>
          <p className="eyebrow">Ваш расклад</p>
          <h1>{result.spreadTitle}</h1>
          {result.question && <p className="question-summary">«{result.question}»</p>}
        </div>
        <StarGuide size="compact" variant="round" />
      </header>

      <div className="reading-cards">
        {result.cards.map((card) => (
          <article className="reading-card" key={`${card.position}-${card.title}`}>
            <div className="reading-card__visual card-reveal-ready" aria-hidden="true">
              <AssetImage
                path={card.image}
                fallbackPath="assets/background/card_back_minimal.webp"
                alt=""
                fallback={<span />}
              />
            </div>
            <div className="reading-card__copy">
              <p>{card.position}</p>
              <h2>{card.title}</h2>
              <span>{card.meaning}</span>
            </div>
          </article>
        ))}
      </div>

      <article className="interpretation">
        <p className="eyebrow">Интерпретация</p>
        <p>{result.interpretation}</p>
      </article>

      <article className="guide-advice">
        <p className="eyebrow">Совет звезды-проводника</p>
        <p>{result.guideAdvice}</p>
      </article>

      <p className="safety-note">{result.disclaimer}</p>

      <div className="result-actions">
        <button className="button button--primary" type="button" onClick={onNewReading}>
          Новый расклад
        </button>
        <button className="button button--ghost" type="button" onClick={onHome}>
          На главную
        </button>
      </div>
    </section>
  );
}
