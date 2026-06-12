from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from bot.keyboards import main_menu
from services.readings.engine import create_draw
from services.tarot.cards import MAJOR_ARCANA, REQUIRED_CARD_FIELDS
from services.tarot.spreads import SPREADS


def _keyboard_has_web_app(markup) -> bool:
    for row in markup.inline_keyboard:
        for button in row:
            if button.web_app is not None:
                return True
    return False


def test_spreads() -> None:
    assert set(SPREADS) == {"daily_card", "quick", "love", "money", "deep"}

    for spread in SPREADS.values():
        drawn_cards = create_draw(spread)
        assert len(drawn_cards) == spread.cards_count

        slugs = [drawn.card.slug for drawn in drawn_cards]
        assert len(slugs) == len(set(slugs))


def test_cards() -> None:
    assert len(MAJOR_ARCANA) == 22

    for card in MAJOR_ARCANA:
        card_data = card.to_dict()
        assert REQUIRED_CARD_FIELDS.issubset(card_data.keys())
        for field_name in REQUIRED_CARD_FIELDS:
            assert card_data[field_name] != ""


def test_main_menu_webapp_url() -> None:
    assert not _keyboard_has_web_app(main_menu(""))
    assert not _keyboard_has_web_app(main_menu("http://localhost:5173"))
    assert not _keyboard_has_web_app(main_menu("https://127.0.0.1"))
    assert _keyboard_has_web_app(main_menu("https://example.com/"))


def main() -> None:
    test_spreads()
    test_cards()
    test_main_menu_webapp_url()
    print("Smoke test passed.")


if __name__ == "__main__":
    main()
