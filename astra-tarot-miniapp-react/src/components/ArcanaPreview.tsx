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
    <section className="arcana-preview" aria-label="РЎС‚Р°СЂС€РёРµ Р°СЂРєР°РЅС‹">
      <div className="section-heading">
        <p className="eyebrow">РЎС‚Р°СЂС€РёРµ Р°СЂРєР°РЅС‹</p>
        <h2>РЎРёРјРІРѕР»С‹, СЃ РєРѕС‚РѕСЂС‹С… РЅР°С‡РёРЅР°РµС‚СЃСЏ РґРёР°Р»РѕРі</h2>
      </div>
      <div className="arcana-carousel" aria-label="РќР°РІРёРіР°С†РёСЏ РїРѕ СЃС‚Р°СЂС€РёРј Р°СЂРєР°РЅР°Рј">
        <button className="arcana-control arcana-control--prev" type="button" onClick={() => scrollByCard(-1)} aria-label="Р›РёСЃС‚Р°С‚СЊ РЅР°Р·Р°Рґ">
          <span className="crescent-icon" aria-hidden="true" />
        </button>
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
        <button className="arcana-control arcana-control--next" type="button" onClick={() => scrollByCard(1)} aria-label="Р›РёСЃС‚Р°С‚СЊ РІРїРµСЂРµРґ">
          <span className="crescent-icon" aria-hidden="true" />
        </button>
      </div>
    </section>
  );
}
