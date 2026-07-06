from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env", override=True, encoding="utf-8-sig")


@dataclass(frozen=True)
class Settings:
    bot_token: str
    gemini_api_key: str
    gemini_model: str
    openrouter_api_key: str
    openrouter_model: str
    openrouter_http_referer: str
    openrouter_x_title: str
    openrouter_timeout_seconds: float
    openrouter_temperature: float
    openrouter_max_tokens_daily: int
    openrouter_max_tokens_quick: int
    openrouter_max_tokens_love: int
    openrouter_max_tokens_money: int
    openrouter_max_tokens_deep: int
    ai_provider: str
    database_path: str
    miniapp_url: str
    public_base_url: str
    host: str
    port: int
    start_backend: bool
    admin_ids: set[int]
    manual_payment_contact: str

    def is_admin(self, user_id: int | None) -> bool:
        return user_id is not None and user_id in self.admin_ids


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _parse_admin_ids(value: str | None) -> set[int]:
    if not value:
        return set()

    admin_ids: set[int] = set()
    for raw_id in value.split(","):
        raw_id = raw_id.strip()
        if not raw_id:
            continue
        try:
            admin_ids.add(int(raw_id))
        except ValueError:
            continue
    return admin_ids


def is_valid_telegram_webapp_url(url: str | None) -> bool:
    if not url:
        return False

    normalized_url = url.strip()
    if not normalized_url.startswith("https://"):
        return False

    parsed = urlparse(normalized_url)
    host = (parsed.hostname or "").lower()
    blocked_hosts = {
        "",
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "your-domain",
        "your-domain-or-hosting-url",
    }
    if host in blocked_hosts:
        return False
    if host.endswith(".localhost"):
        return False

    return True


def load_settings() -> Settings:
    database_path = os.getenv("DATABASE_PATH", "database/astra_tarot.db").strip()
    resolved_database_path = Path(database_path)
    if not resolved_database_path.is_absolute():
        resolved_database_path = ROOT_DIR / resolved_database_path

    return Settings(
        bot_token=os.getenv("BOT_TOKEN", "").strip(),
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip(),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY", "").strip(),
        openrouter_model=os.getenv("OPENROUTER_MODEL", "qwen/qwen3-next-80b-a3b-instruct:free").strip(),
        openrouter_http_referer=os.getenv(
            "OPENROUTER_HTTP_REFERER",
            "https://zarkonai.github.io/astra_tarot/",
        ).strip(),
        openrouter_x_title=os.getenv("OPENROUTER_X_TITLE", "Astra Tarot").strip(),
        openrouter_timeout_seconds=float(os.getenv("OPENROUTER_TIMEOUT_SECONDS", "45")),
        openrouter_temperature=float(os.getenv("OPENROUTER_TEMPERATURE", "0.65")),
        openrouter_max_tokens_daily=int(os.getenv("OPENROUTER_MAX_TOKENS_DAILY", "500")),
        openrouter_max_tokens_quick=int(os.getenv("OPENROUTER_MAX_TOKENS_QUICK", "650")),
        openrouter_max_tokens_love=int(os.getenv("OPENROUTER_MAX_TOKENS_LOVE", "850")),
        openrouter_max_tokens_money=int(os.getenv("OPENROUTER_MAX_TOKENS_MONEY", "850")),
        openrouter_max_tokens_deep=int(os.getenv("OPENROUTER_MAX_TOKENS_DEEP", "1100")),
        ai_provider=os.getenv("AI_PROVIDER", "openrouter").strip().lower(),
        database_path=str(resolved_database_path),
        miniapp_url=os.getenv("MINIAPP_URL", "").strip(),
        public_base_url=os.getenv("PUBLIC_BASE_URL", "").strip(),
        host=os.getenv("HOST", "0.0.0.0").strip(),
        port=int(os.getenv("PORT", "8000")),
        start_backend=_parse_bool(os.getenv("START_BACKEND"), default=True),
        admin_ids=_parse_admin_ids(os.getenv("ADMIN_IDS")),
        manual_payment_contact=os.getenv("MANUAL_PAYMENT_CONTACT", "").strip(),
    )
