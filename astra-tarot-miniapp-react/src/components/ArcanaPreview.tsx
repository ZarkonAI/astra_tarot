import { AssetImage } from "./AssetImage";
import { arcana } from "../data/arcana";

export function ArcanaPreview() {
  return (
    <section className="arcana-preview" aria-label="Старшие арканы">
      <div className="section-heading">
        <p className="eyebrow">Старшие арканы</p>
        <h2>Символы, с которых начинается диалог</h2>
      </div>
      <div className="arcana-strip">
        {arcana.slice(5, 13).map((card) => (
          <div className="arcana-mini-card card-reveal-ready" key={card.slug}>
            <AssetImage
              className="arcana-mini-card__image"
              path={card.image}
              fallbackPath="assets/background/card_back_minimal.webp"
              alt=""
            />
            <span className="arcana-mini-card__number">{card.number}</span>
            <span className="arcana-mini-card__title">{card.title}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
