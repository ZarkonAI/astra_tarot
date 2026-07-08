from __future__ import annotations

from dataclasses import dataclass

from services.tarot.cards import TarotCard, build_public_asset_url
from services.tarot.deck import draw_cards
from services.tarot.spreads import Spread


@dataclass(frozen=True)
class DrawnCard:
    position: str
    card: TarotCard

    def to_prompt_text(self) -> str:
        return (
            f"{self.position}: {self.card.title} - Р°СЂС…РµС‚РёРї {self.card.archetype}; "
            f"СЃРІРµС‚: {self.card.light}; С‚РµРЅСЊ: {self.card.shadow}; СЃРёРјРІРѕР»: {self.card.symbol}."
        )

    def to_public_dict(self, public_base_url: str | None = None) -> dict[str, str | int]:
        card_data: dict[str, str | int] = {
            "position": self.position,
            "number": self.card.number,
            "slug": self.card.slug,
            "title": self.card.title,
            "meaning": self.card.light,
            "light": self.card.light,
            "shadow": self.card.shadow,
            "archetype": self.card.archetype,
            "symbol": self.card.symbol,
            "image_path": self.card.image_path,
        }
        if public_base_url is not None:
            card_data["image"] = build_public_asset_url(public_base_url, self.card.image_path)
        return card_data


def create_draw(spread: Spread) -> list[DrawnCard]:
    cards = draw_cards(spread.cards_count)
    return [DrawnCard(position=position, card=card) for position, card in zip(spread.positions, cards)]

