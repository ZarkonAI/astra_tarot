import { StarGuide } from "./StarGuide";

export function RitualLoader() {
  return (
    <div className="ritual-loader">
      <StarGuide size="compact" />
      <div className="ritual-animation-placeholder animation-placeholder ritual-glow card-reveal-ready guide-float" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>
      <h1>Звезда-проводник выбирает карты...</h1>
      <p>Несколько мгновений, и символы сложатся в мягкий ответ.</p>
    </div>
  );
}
