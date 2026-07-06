from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

VENV_SITE_PACKAGES = ROOT_DIR / ".venv" / "Lib" / "site-packages"
if VENV_SITE_PACKAGES.exists():
    sys.path.insert(0, str(VENV_SITE_PACKAGES))

import httpx
from dotenv import load_dotenv

from bot.config import load_settings
from services.ai.service import _is_bad_ai_text


def _extract_content(data: dict[str, Any]) -> str:
    try:
        content = data["choices"][0]["message"].get("content", "")
    except (KeyError, IndexError, TypeError):
        return ""
    return content.strip() if isinstance(content, str) else ""


async def main() -> None:
    load_dotenv(ROOT_DIR / ".env", override=True, encoding="utf-8-sig")
    settings = load_settings()
    if not settings.openrouter_api_key:
        print("OPENROUTER_API_KEY is empty.")
        return

    payload = {
        "model": settings.openrouter_model,
        "messages": [
            {
                "role": "system",
                "content": "Ответьте только на русском языке, ясно и без технических деталей.",
            },
            {
                "role": "user",
                "content": "Дайте короткую проверочную трактовку карты дня Astra Tarot в 3-4 предложениях. Не используйте латиницу, английские слова и случайные символы.",
            },
        ],
        "temperature": settings.openrouter_temperature,
        "max_tokens": settings.openrouter_max_tokens_quick,
    }
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.openrouter_http_referer,
        "X-Title": settings.openrouter_x_title,
    }

    try:
        async with httpx.AsyncClient(timeout=settings.openrouter_timeout_seconds) as client:
            response = await asyncio.wait_for(
                client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                ),
                timeout=settings.openrouter_timeout_seconds,
            )
    except (httpx.TimeoutException, asyncio.TimeoutError):
        print("status: timeout")
        print(f"model: {settings.openrouter_model}")
        print("response: ")
        return
    except httpx.HTTPError as exc:
        print(f"status: http_error")
        print(f"model: {settings.openrouter_model}")
        print(f"response: {str(exc)[:300]}")
        return

    model_name = settings.openrouter_model
    response_text = response.text.strip()
    if response.headers.get("content-type", "").lower().startswith("application/json"):
        try:
            data = response.json()
            model_name = str(data.get("model") or model_name)
            response_text = _extract_content(data) or response_text
        except ValueError:
            pass

    print(f"status: {response.status_code}")
    print(f"model: {model_name}")
    print(f"response: {response_text[:500]}")
    print(f"quality: {'bad' if _is_bad_ai_text(response_text) else 'ok'}")


if __name__ == "__main__":
    asyncio.run(main())
