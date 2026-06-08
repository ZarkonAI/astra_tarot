import type { CSSProperties } from "react";
import { assetUrl } from "../services/assets";
import type { SpreadConfig } from "../types";

interface SpreadCardProps {
  spread: SpreadConfig;
  isSelected?: boolean;
  isFeatured?: boolean;
  onSelect: (spread: SpreadConfig) => void;
}

export function SpreadCard({ spread, isSelected = false, isFeatured = false, onSelect }: SpreadCardProps) {
  const coverStyle = spread.coverImage
    ? ({
        "--spread-cover": `url("${assetUrl(spread.coverImage)}")`,
      } as CSSProperties & Record<"--spread-cover", string>)
    : undefined;

  return (
    <button
      className={`spread-card ${isSelected ? "is-selected" : ""} ${isFeatured ? "spread-card--featured" : ""}`}
      type="button"
      style={coverStyle}
      onClick={() => onSelect(spread)}
      aria-pressed={isSelected}
    >
      <span className="spread-card__icon" aria-hidden="true">{spread.icon}</span>
      <span className="spread-card__content">
        <span className="spread-card__title">{spread.title}</span>
        <span className="spread-card__description">{spread.description}</span>
        <span className="spread-card__meta">{spread.cardsCount} карт · {spread.priceLabel}</span>
      </span>
    </button>
  );
}
