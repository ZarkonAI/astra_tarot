import { useRef } from "react";
import { AssetImage } from "./AssetImage";
import { arcana } from "../data/arcana";

export function ArcanaPreview() {
  const stripRef = useRef<HTMLDivElement>(null);

  function scrollByCard(direction: -1 | 1) {
    stripRef.current?.scrollBy({
      left: direction * 132,
      behavior: "smooth",
    });
  }

  return (
    <section className="arcana-preview" aria-label="Старшие арканы">
      <div className="section-heading">
        <p className="eyebrow">Старшие арканы</p>
        <h2>Символы, с которых начинается диалог</h2>
      </div>
      <div className="arcana-controls" aria-label="Навигация по старшим арканам">
        <button className="arcana-control" type="button" onClick={() => scrollByCard(-1)} aria-label="Листать назад">
          ‹
        </button>
        <button className="arcana-control" type="button" onClick={() => scrollByCard(1)} aria-label="Листать вперед">
          ›
        </button>
      </div>
      <div className="arcana-strip" ref={stripRef}>
        {arcana.map((card) => (
          <div className="arcana-mini-card card-reveal-ready" key={card.slug}>
            <AssetImage
              className="arcana-mini-card__image"
              path={card.image}
              fallbackPath="assets/background/card_back_minimal.webp"
              alt=""
            />
            <span className="arcana-mini-card__title">{card.title}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
