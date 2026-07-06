from __future__ import annotations

import asyncio
import os
import sys
from tempfile import TemporaryDirectory
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

VENV_SITE_PACKAGES = ROOT_DIR / ".venv" / "Lib" / "site-packages"
if VENV_SITE_PACKAGES.exists():
    sys.path.insert(0, str(VENV_SITE_PACKAGES))

from bot.config import Settings, load_settings
from bot.keyboards import admin_menu, main_menu
from bot.routers.admin import admin_command, admin_reset_callback, reset_me_command
from database.db import Database
from services.ai.service import AIService, _is_bad_ai_text
from services.readings.engine import create_draw
from services.tarot.cards import CARD_BACK_ORNATE, MAJOR_ARCANA, REQUIRED_CARD_FIELDS, build_public_asset_url
from services.tarot.spreads import SPREADS



class FakeUser:
    def __init__(self, user_id: int) -> None:
        self.id = user_id
        self.username = "user"
        self.first_name = "User"
        self.last_name = None
        self.language_code = "ru"


class FakeMessage:
    def __init__(self, user_id: int) -> None:
        self.from_user = FakeUser(user_id)
        self.answers: list[tuple[tuple[object, ...], dict[str, object]]] = []

    async def answer(self, *args, **kwargs) -> None:
        self.answers.append((args, kwargs))


class FakeCallback:
    def __init__(self, user_id: int) -> None:
        self.from_user = FakeUser(user_id)
        self.message = FakeMessage(user_id)
        self.answers: list[tuple[tuple[object, ...], dict[str, object]]] = []

    async def answer(self, *args, **kwargs) -> None:
        self.answers.append((args, kwargs))


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


def test_openrouter_settings() -> None:
    env_keys = [
        "AI_PROVIDER",
        "OPENROUTER_API_KEY",
        "OPENROUTER_MODEL",
        "OPENROUTER_HTTP_REFERER",
        "OPENROUTER_X_TITLE",
        "OPENROUTER_TIMEOUT_SECONDS",
        "OPENROUTER_TEMPERATURE",
        "OPENROUTER_MAX_TOKENS_DAILY",
        "OPENROUTER_MAX_TOKENS_QUICK",
        "OPENROUTER_MAX_TOKENS_LOVE",
        "OPENROUTER_MAX_TOKENS_MONEY",
        "OPENROUTER_MAX_TOKENS_DEEP",
    ]
    old_values = {key: os.environ.get(key) for key in env_keys}
    try:
        os.environ["AI_PROVIDER"] = "openrouter"
        os.environ["OPENROUTER_API_KEY"] = "read-test-key"
        os.environ.pop("OPENROUTER_MODEL", None)
        os.environ.pop("OPENROUTER_HTTP_REFERER", None)
        os.environ.pop("OPENROUTER_X_TITLE", None)
        os.environ.pop("OPENROUTER_TIMEOUT_SECONDS", None)
        os.environ.pop("OPENROUTER_TEMPERATURE", None)
        os.environ.pop("OPENROUTER_MAX_TOKENS_DAILY", None)
        os.environ.pop("OPENROUTER_MAX_TOKENS_QUICK", None)
        os.environ.pop("OPENROUTER_MAX_TOKENS_LOVE", None)
        os.environ.pop("OPENROUTER_MAX_TOKENS_MONEY", None)
        os.environ.pop("OPENROUTER_MAX_TOKENS_DEEP", None)

        settings = load_settings()
        assert settings.openrouter_api_key == "read-test-key"
        assert settings.openrouter_model == "qwen/qwen3-next-80b-a3b-instruct:free"
        assert settings.openrouter_http_referer == "https://zarkonai.github.io/astra_tarot/"
        assert settings.openrouter_x_title == "Astra Tarot"
        assert settings.openrouter_timeout_seconds == 45
        assert settings.openrouter_temperature == 0.65
        assert settings.openrouter_max_tokens_daily == 500
        assert settings.openrouter_max_tokens_quick == 650
        assert settings.openrouter_max_tokens_love == 850
        assert settings.openrouter_max_tokens_money == 850
        assert settings.openrouter_max_tokens_deep == 1100
        assert settings.ai_provider == "openrouter"

        for provider in ("openrouter", "gemini", "local"):
            os.environ["AI_PROVIDER"] = provider
            assert load_settings().ai_provider == provider
    finally:
        for key, value in old_values.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def test_ai_text_quality_filter() -> None:
    good_text = (
        "Это нормальный русский текст для расклада: он звучит ясно, спокойно и последовательно. "
        "В нем достаточно кириллицы, нет странных слов, смешения языков и технических упоминаний."
    )
    assert not _is_bad_ai_text(good_text)
    assert _is_bad_ai_text("residue multiply biome странный короткий текст без нормального смысла")
    assert _is_bad_ai_text("Это текст с 龛 символом, который должен быть отброшен как мусорный ответ модели.")
    assert _is_bad_ai_text("OpenRouter fallback API error ошибка API")


def test_openrouter_max_tokens_by_spread() -> None:
    settings = Settings(
        bot_token="",
        gemini_api_key="",
        gemini_model="gemini-2.5-flash",
        openrouter_api_key="",
        openrouter_model="qwen/qwen3-next-80b-a3b-instruct:free",
        openrouter_http_referer="https://zarkonai.github.io/astra_tarot/",
        openrouter_x_title="Astra Tarot",
        openrouter_timeout_seconds=45,
        openrouter_temperature=0.65,
        openrouter_max_tokens_daily=501,
        openrouter_max_tokens_quick=651,
        openrouter_max_tokens_love=851,
        openrouter_max_tokens_money=852,
        openrouter_max_tokens_deep=1101,
        ai_provider="openrouter",
        database_path="database/astra_tarot.db",
        miniapp_url="https://zarkonai.github.io/astra_tarot/",
        public_base_url="https://zarkonai.github.io/astra_tarot/",
        host="0.0.0.0",
        port=8000,
        start_backend=True,
        admin_ids=set(),
        manual_payment_contact="",
    )
    service = AIService(settings)
    assert service._get_openrouter_max_tokens("daily_card") == 501
    assert service._get_openrouter_max_tokens("quick") == 651
    assert service._get_openrouter_max_tokens("love") == 851
    assert service._get_openrouter_max_tokens("money") == 852
    assert service._get_openrouter_max_tokens("deep") == 1101
    assert service._get_openrouter_max_tokens("unknown") == 800

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
        openrouter_api_key="",
        openrouter_model="openrouter/free",
        openrouter_http_referer="https://zarkonai.github.io/astra_tarot/",
        openrouter_x_title="Astra Tarot",
        openrouter_timeout_seconds=45,
        openrouter_temperature=0.65,
        openrouter_max_tokens_daily=500,
        openrouter_max_tokens_quick=650,
        openrouter_max_tokens_love=850,
        openrouter_max_tokens_money=850,
        openrouter_max_tokens_deep=1100,
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



async def test_admin_silent_for_regular_users() -> None:
    settings = Settings(
        bot_token="",
        gemini_api_key="",
        gemini_model="gemini-2.5-flash",
        openrouter_api_key="",
        openrouter_model="openrouter/free",
        openrouter_http_referer="https://zarkonai.github.io/astra_tarot/",
        openrouter_x_title="Astra Tarot",
        openrouter_timeout_seconds=45,
        openrouter_temperature=0.65,
        openrouter_max_tokens_daily=500,
        openrouter_max_tokens_quick=650,
        openrouter_max_tokens_love=850,
        openrouter_max_tokens_money=850,
        openrouter_max_tokens_deep=1100,
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

    with TemporaryDirectory() as tmp_dir:
        db = Database(str(Path(tmp_dir) / "admin.db"))
        await db.init()
        try:
            admin_message = FakeMessage(987654321)
            reset_message = FakeMessage(987654321)
            callback = FakeCallback(987654321)

            await admin_command(admin_message, settings)
            await reset_me_command(reset_message, settings, db)
            await admin_reset_callback(callback, settings, db)

            assert admin_message.answers == []
            assert reset_message.answers == []
            assert callback.message.answers == []
            assert len(callback.answers) == 1
            assert callback.answers[0][0] == ()
            assert callback.answers[0][1] == {}
        finally:
            await db.close()


async def test_local_fallback_variation() -> None:
    settings = Settings(
        bot_token="",
        gemini_api_key="",
        gemini_model="gemini-2.5-flash",
        openrouter_api_key="",
        openrouter_model="openrouter/free",
        openrouter_http_referer="https://zarkonai.github.io/astra_tarot/",
        openrouter_x_title="Astra Tarot",
        openrouter_timeout_seconds=45,
        openrouter_temperature=0.65,
        openrouter_max_tokens_daily=500,
        openrouter_max_tokens_quick=650,
        openrouter_max_tokens_love=850,
        openrouter_max_tokens_money=850,
        openrouter_max_tokens_deep=1100,
        ai_provider="local",
        database_path="database/astra_tarot.db",
        miniapp_url="https://zarkonai.github.io/astra_tarot/",
        public_base_url="https://zarkonai.github.io/astra_tarot/",
        host="0.0.0.0",
        port=8000,
        start_backend=True,
        admin_ids=set(),
        manual_payment_contact="",
    )
    service = AIService(settings)
    daily_cards = create_draw(SPREADS["daily_card"])
    quick_cards = create_draw(SPREADS["quick"])

    first_user = await service.generate_reading(SPREADS["daily_card"], "", daily_cards, user_id=1001, reading_id=1)
    second_user = await service.generate_reading(SPREADS["daily_card"], "", daily_cards, user_id=1002, reading_id=1)
    quick_text = await service.generate_reading(SPREADS["quick"], "", quick_cards, user_id=1001, reading_id=2)

    assert first_user != second_user
    assert first_user != quick_text

    forbidden_words = ["развлекательный", "рефлексивный", "fallback", "gemini", "openrouter", "ошибка api"]
    for text in (first_user, second_user, quick_text):
        lowered = text.lower()
        for word in forbidden_words:
            assert word not in lowered
async def test_openrouter_empty_key_fallback() -> None:
    settings = Settings(
        bot_token="",
        gemini_api_key="",
        gemini_model="gemini-2.5-flash",
        openrouter_api_key="",
        openrouter_model="openrouter/free",
        openrouter_http_referer="https://zarkonai.github.io/astra_tarot/",
        openrouter_x_title="Astra Tarot",
        openrouter_timeout_seconds=45,
        openrouter_temperature=0.65,
        openrouter_max_tokens_daily=500,
        openrouter_max_tokens_quick=650,
        openrouter_max_tokens_love=850,
        openrouter_max_tokens_money=850,
        openrouter_max_tokens_deep=1100,
        ai_provider="openrouter",
        database_path="database/astra_tarot.db",
        miniapp_url="https://zarkonai.github.io/astra_tarot/",
        public_base_url="https://zarkonai.github.io/astra_tarot/",
        host="0.0.0.0",
        port=8000,
        start_backend=True,
        admin_ids=set(),
        manual_payment_contact="",
    )
    service = AIService(settings)
    drawn_cards = create_draw(SPREADS["daily_card"])
    text = await service.generate_reading(SPREADS["daily_card"], "", drawn_cards, user_id=2001, reading_id=1)
    assert text.strip()
    lowered = text.lower()
    for word in ("gemini", "openrouter", "fallback", "ошибка api"):
        assert word not in lowered


def main() -> None:
    test_spreads()
    test_cards()
    test_openrouter_settings()
    test_ai_text_quality_filter()
    test_openrouter_max_tokens_by_spread()
    test_main_menu_webapp_url()
    test_admin_helpers()
    asyncio.run(test_limit_storage_helpers())
    asyncio.run(test_admin_silent_for_regular_users())
    asyncio.run(test_local_fallback_variation())
    asyncio.run(test_openrouter_empty_key_fallback())
    print("Smoke test passed.")


if __name__ == "__main__":
    main()
