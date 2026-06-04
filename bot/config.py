from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_id: int | None
    database_path: str
    webapp_url: str
    host: str
    port: int
    ai_provider: str
    ai_fallback_1: str | None
    ai_fallback_2: str | None
    ai_fallback_3: str | None
    gemini_api_key: str | None
    gemini_model: str
    groq_api_key: str | None
    groq_model: str
    openrouter_api_key: str | None
    openrouter_model: str
    ollama_base_url: str
    ollama_model: str
    dev_allow_unverified_webapp: bool


def load_settings() -> Settings:
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise RuntimeError("BOT_TOKEN is missing. Add it to .env or hosting environment variables.")

    admin_id_raw = os.getenv("ADMIN_ID", "").strip()
    admin_id = int(admin_id_raw) if admin_id_raw.isdigit() else None

    return Settings(
        bot_token=bot_token,
        admin_id=admin_id,
        database_path=os.getenv("DATABASE_PATH", "database/astra_taro.db"),
        webapp_url=os.getenv("WEBAPP_URL", "http://localhost:8000").rstrip("/"),
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        ai_provider=os.getenv("AI_PROVIDER", "gemini").strip().lower(),
        ai_fallback_1=os.getenv("AI_FALLBACK_1", "groq").strip().lower() or None,
        ai_fallback_2=os.getenv("AI_FALLBACK_2", "openrouter").strip().lower() or None,
        ai_fallback_3=os.getenv("AI_FALLBACK_3", "ollama").strip().lower() or None,
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        groq_api_key=os.getenv("GROQ_API_KEY"),
        groq_model=os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile"),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
        openrouter_model=os.getenv("OPENROUTER_MODEL", "openrouter/auto"),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/"),
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3.1"),
        dev_allow_unverified_webapp=_bool_env("DEV_ALLOW_UNVERIFIED_WEBAPP", True),
    )
