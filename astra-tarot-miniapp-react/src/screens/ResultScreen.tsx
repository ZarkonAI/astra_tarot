import { AssetImage } from "../components/AssetImage";
import { StarGuide } from "../components/StarGuide";
import type { ReadingResult } from "../types";

interface ResultScreenProps {
  result: ReadingResult;
  onHome: () => void;
  onNewReading: () => void;
}

function textParagraphs(value: string): string[] {
  return String(value || "")
    .split(/\n{2,}|\n/)
    .map((line) => line.trim())
    .filter(Boolean);
}

export function ResultScreen({ result, onHome, onNewReading }: ResultScreenProps) {
  const interpretationParagraphs = textParagraphs(result.interpretation);
  const guideAdviceParagraphs = textParagraphs(result.guideAdvice);

  return (
    <section className="screen result-screen screen-enter">
      <header className="result-header">
        <div>
          <p className="eyebrow">Р’Р°С€ СЂР°СЃРєР»Р°Рґ</p>
          <h1>{result.spreadTitle}</h1>
          {result.question ? (
            <p className="question-summary">В«{result.question}В»</p>
          ) : (
            <p className="question-summary">Р‘РµР· РѕС‚РґРµР»СЊРЅРѕРіРѕ РІРѕРїСЂРѕСЃР°. РљР°СЂС‚С‹ СЃРјРѕС‚СЂСЏС‚ РЅР° РѕР±С‰РёР№ С„РѕРЅ РјРѕРјРµРЅС‚Р°.</p>
          )}
        </div>
        <StarGuide size="compact" variant="round" />
      </header>

      <section className="result-oracle-card">
        <StarGuide size="compact" variant="avatar" />
        <div>
          <p className="eyebrow">Р—РІРµР·РґР°-РїСЂРѕРІРѕРґРЅРёРє</p>
          <p>РќРёР¶Рµ СЃРѕР±СЂР°РЅС‹ РІС‹РїР°РІС€РёРµ СЃРёРјРІРѕР»С‹, РёРЅС‚РµСЂРїСЂРµС‚Р°С†РёСЏ Рё РѕРґРёРЅ СЃРїРѕРєРѕР№РЅС‹Р№ СЃР»РµРґСѓСЋС‰РёР№ С€Р°Рі.</p>
        </div>
      </section>

      <div className="reading-cards">
        {result.cards.map((card) => (
          <article className="reading-card" key={`${card.position}-${card.title}`}>
            <div className="reading-card__visual card-reveal-ready" aria-hidden="true">
              <AssetImage
                path={card.image}
                fallbackPath="assets/background/card_back_minimal.webp"
                alt=""
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
        <p className="eyebrow">РРЅС‚РµСЂРїСЂРµС‚Р°С†РёСЏ</p>
        {interpretationParagraphs.map((paragraph) => (
          <p key={paragraph}>{paragraph}</p>
        ))}
      </article>

      {guideAdviceParagraphs.length > 0 && (
        <article className="guide-advice">
          <p className="eyebrow">РЎРѕРІРµС‚ Р·РІРµР·РґС‹-РїСЂРѕРІРѕРґРЅРёРєР°</p>
          {guideAdviceParagraphs.map((paragraph) => (
            <p key={paragraph}>{paragraph}</p>
          ))}
        </article>
      )}

      {result.disclaimer && <p className="safety-note">{result.disclaimer}</p>}

      <div className="result-actions">
        <button className="button button--primary" type="button" onClick={onNewReading}>
          РќРѕРІС‹Р№ СЂР°СЃРєР»Р°Рґ
        </button>
        <button className="button button--ghost" type="button" onClick={onHome}>
          РќР° РіР»Р°РІРЅСѓСЋ
        </button>
      </div>
    </section>
  );
}
