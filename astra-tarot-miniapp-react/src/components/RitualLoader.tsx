import { AssetImage } from "./AssetImage";
import { StarGuide } from "./StarGuide";

interface RitualLoaderProps {
  title?: string;
}

export function RitualLoader({ title = "Звезда выбирает карты..." }: RitualLoaderProps) {
  return (
    <div className="ritual-loader">
      <StarGuide size="compact" variant="card" />
      <div className="ritual-animation-placeholder animation-placeholder ritual-glow card-reveal-ready guide-float" aria-hidden="true">
        <span className="star-pulse">
          <AssetImage path="assets/background/card_back_ornate.webp" alt="" />
        </span>
        <span className="star-pulse">
          <AssetImage path="assets/background/card_back_ornate.webp" alt="" />
        </span>
        <span className="star-pulse">
          <AssetImage path="assets/background/card_back_ornate.webp" alt="" />
        </span>
      </div>
      <h1>{title}</h1>
      <p>Несколько мгновений, и символы сложатся в мягкий ответ.</p>
    </div>
  );
}
