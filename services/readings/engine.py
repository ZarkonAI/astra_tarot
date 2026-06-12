from __future__ import annotations

from dataclasses import dataclass

from services.tarot.cards import TarotCard
from services.tarot.deck import draw_cards
from services.tarot.spreads import Spread


@dataclass(frozen=True)
class DrawnCard:
    position: str
    card: TarotCard

    def to_prompt_text(self) -> str:
        return (
            f"{self.position}: {self.card.title} - архетип {self.card.archetype}; "
            f"свет: {self.card.light}; тень: {self.card.shadow}; символ: {self.card.symbol}."
        )

    def to_public_dict(self) -> dict[str, str | int]:
        return {
            "position": self.position,
            "number": self.card.number,
            "slug": self.card.slug,
            "title": self.card.title,
            "meaning": self.card.light,
            "archetype": self.card.archetype,
            "symbol": self.card.symbol,
        }


def create_draw(spread: Spread) -> list[DrawnCard]:
    cards = draw_cards(spread.cards_count)
    return [DrawnCard(position=position, card=card) for position, card in zip(spread.positions, cards)]
