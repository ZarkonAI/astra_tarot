import { AssetImage } from "./AssetImage";
import { StarGuide } from "./StarGuide";

export function RitualLoader() {
  return (
    <div className="ritual-loader">
      <StarGuide size="compact" variant="card" />
      <div className="ritual-animation-placeholder animation-placeholder ritual-glow card-reveal-ready guide-float" aria-hidden="true">
        <span>
          <AssetImage path="assets/background/card_back_ornate.webp" alt="" />
        </span>
        <span>
          <AssetImage path="assets/background/card_back_ornate.webp" alt="" />
        </span>
        <span>
          <AssetImage path="assets/background/card_back_ornate.webp" alt="" />
        </span>
      </div>
      <h1>Звезда-проводник выбирает карты...</h1>
      <p>Несколько мгновений, и символы сложатся в мягкий ответ.</p>
    </div>
  );
}
