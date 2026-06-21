from __future__ import annotations

import asyncio
import sys
from tempfile import TemporaryDirectory
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

VENV_SITE_PACKAGES = ROOT_DIR / ".venv" / "Lib" / "site-packages"
if VENV_SITE_PACKAGES.exists():
    sys.path.insert(0, str(VENV_SITE_PACKAGES))

from bot.config import Settings
from bot.keyboards import admin_menu, main_menu
from database.db import Database
from services.readings.engine import create_draw
from services.tarot.cards import CARD_BACK_ORNATE, MAJOR_ARCANA, REQUIRED_CARD_FIELDS, build_public_asset_url
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
        assert card.image_path
        assert card.image_path.startswith("assets/")

    for card in MAJOR_ARCANA:
        assert card.image_path != CARD_BACK_ORNATE
        assert card.image_path.startswith("assets/cards/")
        public_file = ROOT_DIR / "astra-tarot-miniapp-react" / "public" / card.image_path
        assert public_file.exists(), f"Missing public asset: {public_file}"

    assert (
        build_public_asset_url("https://zarkonai.github.io/astra_tarot/", "assets/cards/card_judgement.webp")
        == "https://zarkonai.github.io/astra_tarot/assets/cards/card_judgement.webp"
    )

    expected_new_cards = {
        "fool": "assets/cards/card_fool.webp",
        "magician": "assets/cards/card_magician.webp",
        "high_priestess": "assets/cards/card_priestess.webp",
        "empress": "assets/cards/card_empress.webp",
        "emperor": "assets/cards/card_emperor.webp",
    }
    card_paths = {card.slug: card.image_path for card in MAJOR_ARCANA}
    for slug, image_path in expected_new_cards.items():
        assert card_paths[slug] == image_path
        assert (ROOT_DIR / "astra-tarot-miniapp-react" / "public" / image_path).exists()


def test_main_menu_webapp_url() -> None:
    assert not _keyboard_has_web_app(main_menu(""))
    assert not _keyboard_has_web_app(main_menu("http://localhost:5173"))
    assert not _keyboard_has_web_app(main_menu("https://127.0.0.1"))
    assert _keyboard_has_web_app(main_menu("https://zarkonai.github.io/astra_tarot/"))


def test_admin_helpers() -> None:
    settings = Settings(
        bot_token="",
        gemini_api_key="",
        gemini_model="gemini-1.5-flash",
        ai_provider="gemini",
        database_path="database/astra_tarot.db",
        miniapp_url="https://zarkonai.github.io/astra_tarot/",
        public_base_url="https://zarkonai.github.io/astra_tarot/",
        host="0.0.0.0",
        port=8000,
        start_backend=True,
        admin_ids={123456789},
        manual_payment_contact="",
    )
    assert settings.is_admin(123456789)
    assert not settings.is_admin(987654321)
    assert admin_menu().inline_keyboard


async def test_limit_storage_helpers() -> None:
    class TelegramUser:
        id = 987654321
        username = "regular"
        first_name = "Regular"
        last_name = None
        language_code = "ru"

    with TemporaryDirectory() as tmp_dir:
        db = Database(str(Path(tmp_dir) / "smoke.db"))
        await db.init()
        try:
            await db.upsert_user_from_telegram(TelegramUser())
            assert not await db.has_daily_usage(TelegramUser.id)

            await db.mark_daily_usage(TelegramUser.id)
            assert await db.has_daily_usage(TelegramUser.id)

            user = await db.get_user(TelegramUser.id)
            assert user is not None
            assert int(user["has_used_free_full_spread"]) == 0

            await db.mark_free_full_spread_used(TelegramUser.id)
            user = await db.get_user(TelegramUser.id)
            assert user is not None
            assert int(user["has_used_free_full_spread"]) == 1

            await db.reset_user_limits(TelegramUser.id)
            assert not await db.has_daily_usage(TelegramUser.id)
            user = await db.get_user(TelegramUser.id)
            assert user is not None
            assert int(user["has_used_free_full_spread"]) == 0
        finally:
            await db.close()


def main() -> None:
    test_spreads()
    test_cards()
    test_main_menu_webapp_url()
    test_admin_helpers()
    asyncio.run(test_limit_storage_helpers())
    print("Smoke test passed.")


if __name__ == "__main__":
    main()
