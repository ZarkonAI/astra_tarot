import { arcana } from "../data/arcana";

export function ArcanaPreview() {
  return (
    <section className="arcana-preview" aria-label="Старшие арканы">
      <div className="section-heading">
        <p className="eyebrow">Старшие арканы</p>
        <h2>Символы, с которых начинается диалог</h2>
      </div>
      <div className="arcana-strip">
        {arcana.slice(0, 8).map((card) => (
          <div className="arcana-mini-card card-reveal-ready" key={card.slug}>
            <span className="arcana-mini-card__number">{card.number}</span>
            <span className="arcana-mini-card__title">{card.title}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
