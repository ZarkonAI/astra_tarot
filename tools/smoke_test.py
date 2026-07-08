from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

VENV_SITE_PACKAGES = ROOT_DIR / ".venv" / "Lib" / "site-packages"
if VENV_SITE_PACKAGES.exists():
    sys.path.insert(0, str(VENV_SITE_PACKAGES))

from backend.app import create_app
from bot.config import Settings, load_settings
from bot.keyboards import admin_menu, main_menu
from bot.routers.admin import admin_command, admin_reset_callback, reset_me_command
from bot.routers.readings import _random_delay
from database.db import Database
from fastapi.testclient import TestClient
from services.ai.service import AIService, clean_ai_text, _is_bad_ai_text
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


def make_settings(**overrides) -> Settings:
    values = dict(
        bot_token="",
        gemini_api_key="",
        gemini_model="gemini-2.5-flash",
        openrouter_api_key="",
        openrouter_model="qwen/qwen3-next-80b-a3b-instruct:free",
        openrouter_models=[
            "qwen/qwen3-next-80b-a3b-instruct:free",
            "openai/gpt-oss-20b:free",
            "openrouter/free",
        ],
        openrouter_http_referer="https://zarkonai.github.io/astra_tarot/",
        openrouter_x_title="Astra Tarot",
        openrouter_timeout_seconds=45,
        openrouter_temperature=0.65,
        openrouter_cooldown_seconds=60,
        openrouter_max_tokens_daily=500,
        openrouter_max_tokens_quick=650,
        openrouter_max_tokens_love=850,
        openrouter_max_tokens_money=850,
        openrouter_max_tokens_deep=1100,
        ai_provider="openrouter",
        database_path="database/astra_tarot.db",
        miniapp_url="https://zarkonai.github.io/astra_tarot/",
        public_base_url="https://zarkonai.github.io/astra_tarot/",
        cors_allowed_origins=[
            "https://zarkonai.github.io",
            "https://web.telegram.org",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        host="0.0.0.0",
        port=8000,
        start_backend=True,
        admin_ids=set(),
        ritual_delays_enabled=True,
        ritual_card_delay_daily_min=3,
        ritual_card_delay_daily_max=5,
        ritual_card_delay_quick_min=4,
        ritual_card_delay_quick_max=7,
        ritual_card_delay_full_min=6,
        ritual_card_delay_full_max=10,
        ritual_interpretation_delay_min=3,
        ritual_interpretation_delay_max=5,
        admin_skip_ritual_delays=False,
        manual_payment_contact="",
    )
    values.update(overrides)
    return Settings(**values)


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
        assert card.image_path != CARD_BACK_ORNATE
        assert card.image_path.startswith("assets/cards/")
        public_file = ROOT_DIR / "astra-tarot-miniapp-react" / "public" / card.image_path
        assert public_file.exists(), f"Missing public asset: {public_file}"

    assert (
        build_public_asset_url("https://zarkonai.github.io/astra_tarot/", "assets/cards/card_judgement.webp")
        == "https://zarkonai.github.io/astra_tarot/assets/cards/card_judgement.webp"
    )


def _restore_env(old_values: dict[str, str | None]) -> None:
    for key, value in old_values.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def test_openrouter_settings() -> None:
    env_keys = [
        "AI_PROVIDER",
        "OPENROUTER_API_KEY",
        "OPENROUTER_MODELS",
        "OPENROUTER_MODEL",
        "OPENROUTER_HTTP_REFERER",
        "OPENROUTER_X_TITLE",
        "OPENROUTER_TIMEOUT_SECONDS",
        "OPENROUTER_TEMPERATURE",
        "OPENROUTER_COOLDOWN_SECONDS",
        "OPENROUTER_MAX_TOKENS_DAILY",
        "OPENROUTER_MAX_TOKENS_QUICK",
        "OPENROUTER_MAX_TOKENS_LOVE",
        "OPENROUTER_MAX_TOKENS_MONEY",
        "OPENROUTER_MAX_TOKENS_DEEP",
        "CORS_ALLOWED_ORIGINS",
    ]
    old_values = {key: os.environ.get(key) for key in env_keys}
    try:
        os.environ["AI_PROVIDER"] = "openrouter"
        os.environ["OPENROUTER_API_KEY"] = "read-test-key"
        os.environ["OPENROUTER_MODELS"] = " model-a , , model-b,openrouter/free "
        os.environ["OPENROUTER_MODEL"] = "fallback-model"
        os.environ["OPENROUTER_COOLDOWN_SECONDS"] = "77"
        os.environ["CORS_ALLOWED_ORIGINS"] = " https://zarkonai.github.io , http://localhost:5173 "
        for key in env_keys:
            if key not in {"AI_PROVIDER", "OPENROUTER_API_KEY", "OPENROUTER_MODELS", "OPENROUTER_MODEL", "OPENROUTER_COOLDOWN_SECONDS", "CORS_ALLOWED_ORIGINS"}:
                os.environ.pop(key, None)

        settings = load_settings()
        assert settings.openrouter_api_key == "read-test-key"
        assert settings.openrouter_model == "fallback-model"
        assert settings.openrouter_models == ["model-a", "model-b", "openrouter/free"]
        assert settings.openrouter_cooldown_seconds == 77
        assert settings.cors_allowed_origins == ["https://zarkonai.github.io", "http://localhost:5173"]
        assert settings.openrouter_timeout_seconds == 45
        assert settings.openrouter_temperature == 0.65
        assert settings.openrouter_max_tokens_daily == 500
        assert settings.openrouter_max_tokens_quick == 650
        assert settings.openrouter_max_tokens_love == 850
        assert settings.openrouter_max_tokens_money == 850
        assert settings.openrouter_max_tokens_deep == 1100
        assert settings.ai_provider == "openrouter"

        os.environ["OPENROUTER_MODELS"] = ""
        os.environ["OPENROUTER_MODEL"] = "single-model"
        assert load_settings().openrouter_models == ["single-model"]

        os.environ["OPENROUTER_MODEL"] = ""
        assert load_settings().openrouter_models == ["openrouter/free"]

        for provider in ("openrouter", "gemini", "local"):
            os.environ["AI_PROVIDER"] = provider
            assert load_settings().ai_provider == provider
    finally:
        _restore_env(old_values)


def test_ritual_delay_settings() -> None:
    env_keys = [
        "RITUAL_DELAYS_ENABLED",
        "RITUAL_CARD_DELAY_DAILY_MIN",
        "RITUAL_CARD_DELAY_DAILY_MAX",
        "RITUAL_CARD_DELAY_QUICK_MIN",
        "RITUAL_CARD_DELAY_QUICK_MAX",
        "RITUAL_CARD_DELAY_FULL_MIN",
        "RITUAL_CARD_DELAY_FULL_MAX",
        "RITUAL_INTERPRETATION_DELAY_MIN",
        "RITUAL_INTERPRETATION_DELAY_MAX",
        "ADMIN_SKIP_RITUAL_DELAYS",
    ]
    old_values = {key: os.environ.get(key) for key in env_keys}
    try:
        os.environ["RITUAL_DELAYS_ENABLED"] = "true"
        os.environ["RITUAL_CARD_DELAY_DAILY_MIN"] = "1.5"
        os.environ["RITUAL_CARD_DELAY_DAILY_MAX"] = "2.5"
        os.environ["RITUAL_CARD_DELAY_QUICK_MIN"] = "3"
        os.environ["RITUAL_CARD_DELAY_QUICK_MAX"] = "4"
        os.environ["RITUAL_CARD_DELAY_FULL_MIN"] = "5"
        os.environ["RITUAL_CARD_DELAY_FULL_MAX"] = "6"
        os.environ["RITUAL_INTERPRETATION_DELAY_MIN"] = "0.3"
        os.environ["RITUAL_INTERPRETATION_DELAY_MAX"] = "0.7"
        os.environ["ADMIN_SKIP_RITUAL_DELAYS"] = "true"
        settings = load_settings()
        assert settings.ritual_delays_enabled is True
        assert settings.ritual_card_delay_daily_min == 1.5
        assert settings.ritual_card_delay_daily_max == 2.5
        assert settings.ritual_card_delay_quick_min == 3
        assert settings.ritual_card_delay_quick_max == 4
        assert settings.ritual_card_delay_full_min == 5
        assert settings.ritual_card_delay_full_max == 6
        assert settings.ritual_interpretation_delay_min == 0.3
        assert settings.ritual_interpretation_delay_max == 0.7
        assert settings.admin_skip_ritual_delays is True
    finally:
        _restore_env(old_values)


def test_random_delay() -> None:
    first = _random_delay(3, 5, seed="reading-1")
    second = _random_delay(3, 5, seed="reading-1")
    assert 3 <= first <= 5
    assert first == second
    assert 3 <= _random_delay(5, 3, seed="reversed") <= 5


def test_clean_ai_text() -> None:
    dirty = "\u0421\u0443\u0442\u044c \u0441\u0438\u0442\u0443\u0430\u0446\u0438\u0438\n---\n### \u0416\u0440\u0438\u0446\u0430\n- \u0442\u0435\u043a\u0441\u0442\n> \u0435\u0449\u0435 \u0442\u0435\u043a\u0441\u0442\n**\u0412\u0430\u0436\u043d\u043e\u0435**\n```\ncode\n```"
    cleaned = clean_ai_text(dirty)
    assert "**" not in cleaned
    assert "###" not in cleaned
    assert "```" not in cleaned
    assert "---" not in cleaned
    assert all(not line.startswith("- ") for line in cleaned.splitlines())
    assert "\u0416\u0440\u0438\u0446\u0430" in cleaned
    assert "\u0442\u0435\u043a\u0441\u0442" in cleaned
    assert clean_ai_text("\u041d\u043e\u0440\u043c\u0430\u043b\u044c\u043d\u043e\u0435 \u0440\u0443\u0441\u0441\u043a\u043e\u0435 \u0442\u0438\u0440\u0435 \u2014 \u0432\u043d\u0443\u0442\u0440\u0438 \u043f\u0440\u0435\u0434\u043b\u043e\u0436\u0435\u043d\u0438\u044f") == "\u041d\u043e\u0440\u043c\u0430\u043b\u044c\u043d\u043e\u0435 \u0440\u0443\u0441\u0441\u043a\u043e\u0435 \u0442\u0438\u0440\u0435 \u2014 \u0432\u043d\u0443\u0442\u0440\u0438 \u043f\u0440\u0435\u0434\u043b\u043e\u0436\u0435\u043d\u0438\u044f"


def test_ai_text_quality_filter() -> None:
    good_text = (
        "\u042d\u0442\u043e \u043d\u043e\u0440\u043c\u0430\u043b\u044c\u043d\u044b\u0439 \u0440\u0443\u0441\u0441\u043a\u0438\u0439 \u0442\u0435\u043a\u0441\u0442 \u0434\u043b\u044f \u0440\u0430\u0441\u043a\u043b\u0430\u0434\u0430. "
        "\u041e\u043d \u0437\u0432\u0443\u0447\u0438\u0442 \u044f\u0441\u043d\u043e, \u0441\u043f\u043e\u043a\u043e\u0439\u043d\u043e \u0438 \u043f\u043e\u0441\u043b\u0435\u0434\u043e\u0432\u0430\u0442\u0435\u043b\u044c\u043d\u043e. "
        "\u0412 \u043d\u0435\u043c \u0434\u043e\u0441\u0442\u0430\u0442\u043e\u0447\u043d\u043e \u043a\u0438\u0440\u0438\u043b\u043b\u0438\u0446\u044b, \u043d\u0435\u0442 \u0441\u0442\u0440\u0430\u043d\u043d\u044b\u0445 \u0441\u043b\u043e\u0432, "
        "\u0441\u043c\u0435\u0448\u0435\u043d\u0438\u044f \u044f\u0437\u044b\u043a\u043e\u0432 \u0438 \u0442\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0438\u0445 \u0443\u043f\u043e\u043c\u0438\u043d\u0430\u043d\u0438\u0439."
    )
    assert not _is_bad_ai_text(good_text)
    assert _is_bad_ai_text("residue multiply biome \u0441\u0442\u0440\u0430\u043d\u043d\u044b\u0439 \u0442\u0435\u043a\u0441\u0442")
    assert _is_bad_ai_text("\u042d\u0442\u043e \u0442\u0435\u043a\u0441\u0442 \u0441 \u9f9b \u0441\u0438\u043c\u0432\u043e\u043b\u043e\u043c, \u043a\u043e\u0442\u043e\u0440\u044b\u0439 \u0434\u043e\u043b\u0436\u0435\u043d \u0431\u044b\u0442\u044c \u043e\u0442\u0431\u0440\u043e\u0448\u0435\u043d.")
    assert _is_bad_ai_text("OpenRouter fallback API error \u043e\u0448\u0438\u0431\u043a\u0430 API")
    assert _is_bad_ai_text("Thus \u044d\u0442\u043e \u0441\u043b\u043e\u0432\u043e \u0434\u043e\u043b\u0436\u043d\u043e \u043e\u0442\u043a\u043b\u043e\u043d\u0438\u0442\u044c \u043e\u0442\u0432\u0435\u0442, \u0434\u0430\u0436\u0435 \u0435\u0441\u043b\u0438 \u0440\u044f\u0434\u043e\u043c \u0435\u0441\u0442\u044c \u0440\u0443\u0441\u0441\u043a\u0438\u0439 \u0442\u0435\u043a\u0441\u0442.")
    assert _is_bad_ai_text("\u042d\u0442\u043e \u0440\u0443\u0441\u0441\u043a\u0438\u0439 \u0442\u0435\u043a\u0441\u0442 \u0441 \u0438\u0432\u0440\u0438\u0442\u043e\u043c \u05e2\u05dc \u0432\u043d\u0443\u0442\u0440\u0438, \u043f\u043e\u044d\u0442\u043e\u043c\u0443 \u043e\u043d \u0434\u043e\u043b\u0436\u0435\u043d \u0431\u044b\u0442\u044c \u043e\u0442\u043a\u043b\u043e\u043d\u0435\u043d.")
    assert _is_bad_ai_text("### \u0417\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a\n\u0420\u0443\u0441\u0441\u043a\u0438\u0439 \u0442\u0435\u043a\u0441\u0442 \u0441 markdown-\u0437\u0430\u0433\u043e\u043b\u043e\u0432\u043a\u043e\u043c \u0434\u043e\u043b\u0436\u0435\u043d \u0431\u044b\u0442\u044c \u043e\u0442\u043a\u043b\u043e\u043d\u0435\u043d.")
    assert _is_bad_ai_text("Behavior? (But we must not use English. Let's rephrase...) \u042d\u0442\u043e \u043f\u043b\u043e\u0445\u043e\u0439 \u0442\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0438\u0439 \u0442\u0435\u043a\u0441\u0442.")


def test_openrouter_helpers() -> None:
    settings = make_settings(
        openrouter_max_tokens_daily=501,
        openrouter_max_tokens_quick=651,
        openrouter_max_tokens_love=851,
        openrouter_max_tokens_money=852,
        openrouter_max_tokens_deep=1101,
        openrouter_cooldown_seconds=60,
    )
    service = AIService(settings)
    assert service._get_openrouter_max_tokens("daily_card") == 501
    assert service._get_openrouter_max_tokens("quick") == 651
    assert service._get_openrouter_max_tokens("love") == 851
    assert service._get_openrouter_max_tokens("money") == 852
    assert service._get_openrouter_max_tokens("deep") == 1101
    assert service._get_openrouter_max_tokens("unknown") == 800

    service._put_openrouter_model_in_cooldown("model-a")
    assert service._is_openrouter_model_in_cooldown("model-a")
    assert not service._is_openrouter_model_in_cooldown("model-b")


def test_main_menu_webapp_url() -> None:
    assert not _keyboard_has_web_app(main_menu(""))
    assert not _keyboard_has_web_app(main_menu("http://localhost:5173"))
    assert not _keyboard_has_web_app(main_menu("https://127.0.0.1"))
    assert _keyboard_has_web_app(main_menu("https://zarkonai.github.io/astra_tarot/"))


def test_admin_helpers() -> None:
    settings = make_settings(ai_provider="gemini", admin_ids={123456789})
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

            reading_id = await db.create_reading(
                telegram_id=TelegramUser.id,
                spread_slug="daily_card",
                spread_title="РљР°СЂС‚Р° РґРЅСЏ",
                question="",
                cards=[],
                response_text="",
                is_free=True,
            )
            await db.update_reading_response(reading_id, "Р“РѕС‚РѕРІР°СЏ С‚СЂР°РєС‚РѕРІРєР°")

            await db.reset_user_limits(TelegramUser.id)
            assert not await db.has_daily_usage(TelegramUser.id)
            user = await db.get_user(TelegramUser.id)
            assert user is not None
            assert int(user["has_used_free_full_spread"]) == 0
        finally:
            await db.close()


async def test_admin_silent_for_regular_users() -> None:
    settings = make_settings(ai_provider="gemini", admin_ids={123456789})
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
    service = AIService(make_settings(ai_provider="local"))
    daily_cards = create_draw(SPREADS["daily_card"])
    quick_cards = create_draw(SPREADS["quick"])

    first_user = await service.generate_reading(SPREADS["daily_card"], "", daily_cards, user_id=1001, reading_id=1)
    second_user = await service.generate_reading(SPREADS["daily_card"], "", daily_cards, user_id=1002, reading_id=1)
    quick_text = await service.generate_reading(SPREADS["quick"], "", quick_cards, user_id=1001, reading_id=2)

    assert first_user.strip()
    assert second_user.strip()
    assert quick_text.strip()
    assert first_user != quick_text

    forbidden_words = ["fallback", "gemini", "openrouter", "РѕС€РёР±РєР° api"]
    for text in (first_user, second_user, quick_text):
        lowered = text.lower()
        for word in forbidden_words:
            assert word not in lowered


async def test_openrouter_empty_key_fallback() -> None:
    service = AIService(make_settings(ai_provider="openrouter", openrouter_api_key=""))
    drawn_cards = create_draw(SPREADS["daily_card"])
    text = await service.generate_reading(SPREADS["daily_card"], "", drawn_cards, user_id=2001, reading_id=1)
    assert text.strip()
    lowered = text.lower()
    for word in ("gemini", "openrouter", "fallback", "РѕС€РёР±РєР° api"):
        assert word not in lowered


async def test_backend_api_create_reading() -> None:
    with TemporaryDirectory() as tmp_dir:
        db = Database(str(Path(tmp_dir) / "backend.db"))
        await db.init()
        try:
            settings = make_settings(
                ai_provider="local",
                database_path=str(Path(tmp_dir) / "backend.db"),
                public_base_url="https://zarkonai.github.io/astra_tarot/",
            )
            app = create_app(settings, db, AIService(settings))
            client = TestClient(app)

            health = client.get("/health")
            assert health.status_code == 200
            assert health.json() == {"ok": True, "service": "astra-tarot-backend"}

            response = client.post(
                "/api/readings/create",
                json={
                    "spread": "daily_card",
                    "question": "",
                    "initData": "test-init-data",
                    "telegramUser": {"id": 0, "first_name": "Browser"},
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["ok"] is True
            assert data["spread"] == "daily_card"
            assert data["cards"]
            assert data["cards"][0]["image"].startswith("https://zarkonai.github.io/astra_tarot/assets/cards/")
            assert data["interpretation"].strip()
        finally:
            await db.close()
def main() -> None:
    test_spreads()
    test_cards()
    test_openrouter_settings()
    test_ritual_delay_settings()
    test_random_delay()
    test_clean_ai_text()
    test_ai_text_quality_filter()
    test_openrouter_helpers()
    test_main_menu_webapp_url()
    test_admin_helpers()
    asyncio.run(test_limit_storage_helpers())
    asyncio.run(test_admin_silent_for_regular_users())
    asyncio.run(test_local_fallback_variation())
    asyncio.run(test_openrouter_empty_key_fallback())
    asyncio.run(test_backend_api_create_reading())
    print("Smoke test passed.")


if __name__ == "__main__":
    main()







