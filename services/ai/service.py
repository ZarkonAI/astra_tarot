from __future__ import annotations

import asyncio
import logging
import random
import re
import time
from datetime import datetime, timezone
from typing import Any

import httpx

from bot.config import Settings
from services.ai.prompts import build_reading_prompt
from services.readings.engine import DrawnCard
from services.tarot.spreads import Spread


logger = logging.getLogger(__name__)


class OpenRouterTimeoutError(RuntimeError):
    pass


class OpenRouterLowQualityTextError(RuntimeError):
    pass


class OpenRouterAuthenticationError(RuntimeError):
    pass


def _short_error(exc: Exception) -> str:
    message = str(exc).strip() or exc.__class__.__name__
    message = message.replace("\n", " ").replace("\r", " ")
    return message[:240]


def _short_response_text(response: httpx.Response) -> str:
    text = response.text.strip().replace("\n", " ").replace("\r", " ")
    return text[:180] or "empty response"


def _clean_text(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        repaired = text.encode("cp1251").decode("utf-8")
    except UnicodeError:
        return text
    return repaired if repaired.count("пїЅ") <= text.count("пїЅ") else text


def _extract_openrouter_content(data: dict[str, Any]) -> str:
    try:
        content = data["choices"][0]["message"].get("content", "")
    except (KeyError, IndexError, TypeError):
        return ""
    if not isinstance(content, str):
        return ""
    return content.strip()


_HEBREW_RE = re.compile(r"[\u0590-\u05FF]")
_CJK_RE = re.compile(r"[\u3400-\u4DBF\u4E00-\u9FFF\u3040-\u30FF\uAC00-\uD7AF]")
_CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")
_LATIN_RE = re.compile(r"[A-Za-z]")
_MARKDOWN_LINE_RE = re.compile(r"(^|\n)\s*(?:#{1,6}\s+|[-*]\s+|>\s+)")
_BAD_AI_MARKERS = (
    "**",
    "###",
    "```",
    "thus",
    "residue",
    "multiply",
    "biome",
    "arqu\u00e9tique",
    "arquetique",
    "\u043d\u0435\u0439\u0442\u0440\u043e\u0441\u0444\u0435\u0440",
    "\u0442\u0430\u043d\u0446\u0435\u0442",
    "\u9f9b",
    "openrouter",
    "gemini",
    "fallback",
    "api error",
    "behavior",
    "let's rephrase",
    "rephrase",
    "we must not use",
    "english",
    "hebrew",
    "but we must",
    "(but",
    "\u043d\u0435 \u0438\u0441\u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u044c english",    "\u043e\u0448\u0438\u0431\u043a\u0430 api",
)


def clean_ai_text(text: str) -> str:
    cleaned = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
    if not cleaned.strip():
        return ""

    cleaned = re.sub(r"```[\s\S]*?```", "", cleaned)
    cleaned = re.sub(r"`([^`]*)`", r"\1", cleaned)
    cleaned = re.sub(r"\*\*([^*\n]+)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"__([^_\n]+)__", r"\1", cleaned)
    cleaned = cleaned.replace("**", "").replace("__", "")

    result_lines: list[str] = []
    for raw_line in cleaned.split("\n"):
        line = raw_line.rstrip()
        if re.fullmatch(r"\s*(?:-{3,}|_{3,}|\*{3,})\s*", line):
            result_lines.append("")
            continue
        line = re.sub(r"^\s{0,3}#{1,6}\s*", "", line)
        line = re.sub(r"^\s*>\s?", "", line)
        line = re.sub(r"^\s*[-*\u2022]\s+", "", line)
        line = re.sub(r"^\s*\d+[.)]\s+", "", line)
        result_lines.append(line.strip())

    compact_lines: list[str] = []
    previous_blank = False
    for line in result_lines:
        if not line:
            if not previous_blank:
                compact_lines.append("")
            previous_blank = True
            continue
        compact_lines.append(line)
        previous_blank = False

    return "\n".join(compact_lines).strip()


def _is_bad_ai_text(text: str) -> bool:
    normalized = str(text or "").strip()
    if not normalized:
        return True

    lowered = normalized.lower()
    if any(marker in lowered for marker in _BAD_AI_MARKERS):
        return True
    if re.search(r"\bapi\b", lowered):
        return True
    if _MARKDOWN_LINE_RE.search(normalized):
        return True
    if _HEBREW_RE.search(normalized) or _CJK_RE.search(normalized):
        return True

    cyrillic_letters = len(_CYRILLIC_RE.findall(normalized))
    latin_letters = len(_LATIN_RE.findall(normalized))
    if cyrillic_letters < 25:
        return True
    return latin_letters > max(6, cyrillic_letters * 0.05)


def _openrouter_response_structure(spread_slug: str) -> str:
    structures = {
        "daily_card": "2-4 РєРѕСЂРѕС‚РєРёС… Р°Р±Р·Р°С†Р° Р±РµР· СЃРїРёСЃРєРѕРІ: РіР»Р°РІРЅС‹Р№ СЃРјС‹СЃР» РєР°СЂС‚С‹, РјСЏРіРєРёР№ СЃРѕРІРµС‚ РЅР° РґРµРЅСЊ Рё С‚РѕС‡РєР° РІРЅРёРјР°РЅРёСЏ.",
        "quick": "РљРѕСЂРѕС‚РєРѕРµ РІСЃС‚СѓРїР»РµРЅРёРµ, СЃРјС‹СЃР» РєР°СЂС‚С‹ РёР»Рё РєР°СЂС‚, СЏСЃРЅС‹Р№ РїСЂР°РєС‚РёС‡РЅС‹Р№ СЃРѕРІРµС‚ Р±РµР· РґР»РёРЅРЅС‹С… СЃРїРёСЃРєРѕРІ.",
        "love": "РњСЏРіРєРёР№ СЌРјРѕС†РёРѕРЅР°Р»СЊРЅС‹Р№ СЃС‚РёР»СЊ: С‡СѓРІСЃС‚РІР°, РєРѕРЅС‚Р°РєС‚, РіСЂР°РЅРёС†С‹ Рё Р±РµСЂРµР¶РЅС‹Р№ СЃР»РµРґСѓСЋС‰РёР№ С€Р°Рі.",
        "money": "РџСЂР°РєС‚РёС‡РЅС‹Р№ СЃС‚РёР»СЊ: СЂРµСЃСѓСЂСЃС‹, СЂРµС€РµРЅРёСЏ, СЂРёСЃРєРё Рё Р±Р»РёР¶Р°Р№С€РёР№ С€Р°Рі Р±РµР· С„РёРЅР°РЅСЃРѕРІС‹С… РіР°СЂР°РЅС‚РёР№.",
        "deep": "4-6 РїРѕРЅСЏС‚РЅС‹С… Р°Р±Р·Р°С†РµРІ: СЃСѓС‚СЊ СЃРёС‚СѓР°С†РёРё, СЃРєСЂС‹С‚С‹Р№ С„Р°РєС‚РѕСЂ, РѕРїРѕСЂР°, РїСЂРµРїСЏС‚СЃС‚РІРёРµ Рё СЃР»РµРґСѓСЋС‰РёР№ С€Р°Рі.",
    }
    return structures.get(spread_slug, structures["quick"])


class AIService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._local_provider_logged = False
        self._openrouter_model_cooldowns: dict[str, float] = {}

    async def generate_reading(
        self,
        spread: Spread,
        question: str,
        drawn_cards: list[DrawnCard],
        user_id: int | None = None,
        reading_id: int | None = None,
    ) -> str:
        provider = self._settings.ai_provider
        if provider == "local":
            if not self._local_provider_logged:
                logger.warning("AI provider is local; using local fallback.")
                self._local_provider_logged = True
            return self._fallback_reading(spread, question, drawn_cards, user_id=user_id, reading_id=reading_id)

        if provider == "openrouter":
            try:
                return await self._generate_with_openrouter(spread, question, drawn_cards)
            except OpenRouterAuthenticationError:
                logger.warning("OpenRouter authentication failed; using local fallback.")
            except OpenRouterTimeoutError:
                logger.warning("OpenRouter timeout; using local fallback.")
                logger.debug("OpenRouter timeout traceback", exc_info=True)
            except OpenRouterLowQualityTextError:
                logger.warning("OpenRouter models unavailable; using local fallback.")
                logger.debug("OpenRouter low-quality text traceback", exc_info=True)
            except Exception as exc:
                logger.warning("OpenRouter models unavailable; using local fallback. Reason: %s", _short_error(exc))
                logger.debug("OpenRouter request traceback", exc_info=True)
            return self._fallback_reading(spread, question, drawn_cards, user_id=user_id, reading_id=reading_id)

        if provider == "gemini":
            try:
                return await self._generate_with_gemini(spread, question, drawn_cards)
            except Exception as exc:
                logger.warning("Gemini request failed; using local fallback. Reason: %s", _short_error(exc))
                logger.debug("Gemini request traceback", exc_info=True)
            return self._fallback_reading(spread, question, drawn_cards, user_id=user_id, reading_id=reading_id)

        logger.warning("Unknown AI_PROVIDER=%s; using local fallback.", provider)
        return self._fallback_reading(spread, question, drawn_cards, user_id=user_id, reading_id=reading_id)

    async def _generate_with_openrouter(
        self,
        spread: Spread,
        question: str,
        drawn_cards: list[DrawnCard],
    ) -> str:
        if not self._settings.openrouter_api_key:
            raise RuntimeError("OpenRouter API key is empty")

        models = self._settings.openrouter_models or [self._settings.openrouter_model or "openrouter/free"]
        available_models = [model for model in models if not self._is_openrouter_model_in_cooldown(model)]
        if not available_models:
            logger.warning("OpenRouter models are in cooldown; using local fallback.")
            raise OpenRouterLowQualityTextError("all OpenRouter models are in cooldown")

        for model in available_models:
            for is_retry in (False, True):
                payload = self._build_openrouter_payload(model, spread, question, drawn_cards, is_retry=is_retry)
                try:
                    response = await self._post_openrouter(payload)
                except OpenRouterTimeoutError:
                    logger.warning("OpenRouter model timeout: %s", model)
                    break
                except httpx.HTTPError as exc:
                    logger.warning("OpenRouter network error for model %s: %s", model, _short_error(exc))
                    break

                if response.status_code == 401:
                    logger.warning("OpenRouter authentication failed")
                    raise OpenRouterAuthenticationError("OpenRouter authentication failed")
                if response.status_code == 429:
                    self._put_openrouter_model_in_cooldown(model)
                    logger.warning("OpenRouter model rate limited: %s; trying next model", model)
                    break
                if response.status_code >= 500:
                    logger.warning("OpenRouter model server error: %s status=%s", model, response.status_code)
                    break
                if response.status_code != 200:
                    logger.warning(
                        "OpenRouter model failed: %s status=%s response=%s",
                        model,
                        response.status_code,
                        _short_response_text(response),
                    )
                    break

                try:
                    data = response.json()
                except ValueError:
                    logger.warning("OpenRouter model returned invalid JSON: %s", model)
                    break

                content = clean_ai_text(_extract_openrouter_content(data))
                if not _is_bad_ai_text(content):
                    logger.info("OpenRouter model used: %s", data.get("model", model))
                    return content

                logger.warning("OpenRouter text quality rejected: %s", model)
                if is_retry:
                    break

        logger.warning("OpenRouter models unavailable; using local fallback")
        raise OpenRouterLowQualityTextError("OpenRouter models unavailable")

    def _build_openrouter_payload(
        self,
        model: str,
        spread: Spread,
        question: str,
        drawn_cards: list[DrawnCard],
        is_retry: bool,
    ) -> dict[str, Any]:
        return {
            "model": model,
            "messages": [
                {"role": "system", "content": self._openrouter_system_prompt()},
                {
                    "role": "user",
                    "content": self._openrouter_user_prompt(spread, question, drawn_cards, is_retry=is_retry),
                },
            ],
            "temperature": self._settings.openrouter_temperature,
            "max_tokens": self._get_openrouter_max_tokens(spread.slug),
        }

    async def _post_openrouter(self, payload: dict[str, Any]) -> httpx.Response:
        headers = {
            "Authorization": f"Bearer {self._settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self._settings.openrouter_http_referer,
            "X-Title": self._settings.openrouter_x_title,
        }

        try:
            async with httpx.AsyncClient(timeout=self._settings.openrouter_timeout_seconds) as client:
                return await asyncio.wait_for(
                    client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers=headers,
                        json=payload,
                    ),
                    timeout=self._settings.openrouter_timeout_seconds,
                )
        except (httpx.TimeoutException, asyncio.TimeoutError) as exc:
            raise OpenRouterTimeoutError("OpenRouter request timed out") from exc

    def _put_openrouter_model_in_cooldown(self, model: str) -> None:
        cooldown_seconds = max(0, self._settings.openrouter_cooldown_seconds)
        self._openrouter_model_cooldowns[model] = time.monotonic() + cooldown_seconds

    def _is_openrouter_model_in_cooldown(self, model: str) -> bool:
        cooldown_until = self._openrouter_model_cooldowns.get(model)
        if cooldown_until is None:
            return False
        if time.monotonic() < cooldown_until:
            return True
        self._openrouter_model_cooldowns.pop(model, None)
        return False

    def _get_openrouter_max_tokens(self, spread_id: str) -> int:
        max_tokens_by_spread = {
            "daily_card": self._settings.openrouter_max_tokens_daily,
            "quick": self._settings.openrouter_max_tokens_quick,
            "love": self._settings.openrouter_max_tokens_love,
            "money": self._settings.openrouter_max_tokens_money,
            "deep": self._settings.openrouter_max_tokens_deep,
        }
        return max_tokens_by_spread.get(spread_id, 800)

    @staticmethod
    def _openrouter_system_prompt() -> str:
        response_headings = AIService._strict_response_headings()
        return (
            "\u0422\u044b \u043c\u044f\u0433\u043a\u0438\u0439 \u0440\u0443\u0441\u0441\u043a\u043e\u044f\u0437\u044b\u0447\u043d\u044b\u0439 \u0438\u043d\u0442\u0435\u0440\u043f\u0440\u0435\u0442\u0430\u0442\u043e\u0440 \u0441\u0438\u043c\u0432\u043e\u043b\u0438\u0447\u0435\u0441\u043a\u0438\u0445 \u0440\u0430\u0441\u043a\u043b\u0430\u0434\u043e\u0432 Astra Tarot. "
            "\u041f\u0438\u0448\u0438 \u0442\u043e\u043b\u044c\u043a\u043e \u043e\u0431\u044b\u0447\u043d\u044b\u043c \u0440\u0443\u0441\u0441\u043a\u0438\u043c \u0442\u0435\u043a\u0441\u0442\u043e\u043c. "
            "\u041d\u0435 \u0438\u0441\u043f\u043e\u043b\u044c\u0437\u0443\u0439 Markdown. "
            "\u041d\u0435 \u0438\u0441\u043f\u043e\u043b\u044c\u0437\u0443\u0439 \u0441\u0438\u043c\u0432\u043e\u043b\u044b \u0444\u043e\u0440\u043c\u0430\u0442\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u044f: **, __, ###, ##, #, ---, >, -, *, `. "
            "\u041d\u0435 \u0434\u0435\u043b\u0430\u0439 \u0437\u0430\u0433\u043e\u043b\u043e\u0432\u043a\u0438 \u0447\u0435\u0440\u0435\u0437 Markdown. "
            "\u041d\u0435 \u0434\u0435\u043b\u0430\u0439 \u0441\u043f\u0438\u0441\u043a\u0438 \u0447\u0435\u0440\u0435\u0437 \u0434\u0435\u0444\u0438\u0441\u044b \u0438\u043b\u0438 \u043d\u0443\u043c\u0435\u0440\u0430\u0446\u0438\u044e. "
            "\u041d\u0435 \u0438\u0441\u043f\u043e\u043b\u044c\u0437\u0443\u0439 \u0430\u043d\u0433\u043b\u0438\u0439\u0441\u043a\u0438\u0435 \u0441\u043b\u043e\u0432\u0430, \u043b\u0430\u0442\u0438\u043d\u0438\u0446\u0443, \u0438\u0432\u0440\u0438\u0442, \u043a\u0438\u0442\u0430\u0439\u0441\u043a\u0438\u0435, \u044f\u043f\u043e\u043d\u0441\u043a\u0438\u0435 \u0438\u043b\u0438 \u043a\u043e\u0440\u0435\u0439\u0441\u043a\u0438\u0435 \u0441\u0438\u043c\u0432\u043e\u043b\u044b. "
            "\u041d\u0435 \u0438\u0441\u043f\u043e\u043b\u044c\u0437\u0443\u0439 \u0442\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0438\u0435 \u0441\u043b\u043e\u0432\u0430: OpenRouter, Gemini, fallback, API. "
            "\u041d\u0435 \u0434\u043e\u0431\u0430\u0432\u043b\u044f\u0439 \u0434\u0438\u0441\u043a\u043b\u0435\u0439\u043c\u0435\u0440\u044b. "
            "\u0424\u043e\u0440\u043c\u0430\u0442\u0438\u0440\u0443\u0439 \u0442\u0435\u043a\u0441\u0442 \u043f\u0440\u043e\u0441\u0442\u044b\u043c\u0438 \u0441\u0442\u0440\u043e\u043a\u0430\u043c\u0438. "
            "\u0414\u043b\u044f \u0440\u0430\u0437\u0434\u0435\u043b\u043e\u0432 \u0438\u0441\u043f\u043e\u043b\u044c\u0437\u0443\u0439 \u043e\u0431\u044b\u0447\u043d\u044b\u0435 \u0437\u0430\u0433\u043e\u043b\u043e\u0432\u043a\u0438 \u0431\u0435\u0437 \u0441\u043f\u0435\u0446\u0441\u0438\u043c\u0432\u043e\u043b\u043e\u0432: "
            + ", ".join(response_headings)
            + "."
        )

    @staticmethod
    def _strict_response_headings() -> tuple[str, ...]:
        return (
            "\u0421\u0443\u0442\u044c \u0441\u0438\u0442\u0443\u0430\u0446\u0438\u0438",
            "\u0421\u043a\u0440\u044b\u0442\u044b\u0439 \u0444\u0430\u043a\u0442\u043e\u0440",
            "\u0427\u0442\u043e \u043f\u043e\u043c\u043e\u0433\u0430\u0435\u0442",
            "\u0427\u0442\u043e \u043c\u0435\u0448\u0430\u0435\u0442",
            "\u0421\u043b\u0435\u0434\u0443\u044e\u0449\u0438\u0439 \u0448\u0430\u0433",
        )

    @staticmethod
    def _openrouter_user_prompt(
        spread: Spread,
        question: str,
        drawn_cards: list[DrawnCard],
        is_retry: bool = False,
    ) -> str:
        question_text = question.strip() or "\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c \u043d\u0435 \u0443\u043a\u0430\u0437\u0430\u043b \u043e\u0442\u0434\u0435\u043b\u044c\u043d\u044b\u0439 \u0432\u043e\u043f\u0440\u043e\u0441."
        card_blocks = []
        for drawn in drawn_cards:
            card_blocks.append(
                "\n".join(
                    [
                        f"\u041f\u043e\u0437\u0438\u0446\u0438\u044f: {_clean_text(drawn.position)}",
                        f"\u041a\u0430\u0440\u0442\u0430: {_clean_text(drawn.card.title)}",
                        f"\u0421\u0432\u0435\u0442\u043b\u043e\u0435 \u0437\u043d\u0430\u0447\u0435\u043d\u0438\u0435: {_clean_text(drawn.card.light)}",
                        f"\u0422\u0435\u043d\u0435\u0432\u0430\u044f \u043f\u043e\u0434\u0441\u043a\u0430\u0437\u043a\u0430: {_clean_text(drawn.card.shadow)}",
                        f"\u0421\u0438\u043c\u0432\u043e\u043b: {_clean_text(drawn.card.symbol)}",
                        f"\u0410\u0440\u0445\u0435\u0442\u0438\u043f: {_clean_text(drawn.card.archetype)}",
                    ]
                )
            )
        retry_text = (
            "\u041f\u0440\u0435\u0434\u044b\u0434\u0443\u0449\u0438\u0439 \u043e\u0442\u0432\u0435\u0442 \u0431\u044b\u043b \u043e\u0442\u043a\u043b\u043e\u043d\u0435\u043d \u0438\u0437 \u0437\u0430 \u043a\u0430\u0447\u0435\u0441\u0442\u0432\u0430. \u0412\u0435\u0440\u043d\u0438 \u0442\u043e\u043b\u044c\u043a\u043e \u0447\u0438\u0441\u0442\u044b\u0439 \u0440\u0443\u0441\u0441\u043a\u0438\u0439 \u0442\u0435\u043a\u0441\u0442.\n\n"
            if is_retry
            else ""
        )
        return (
            f"{retry_text}"
            f"\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u0440\u0430\u0441\u043a\u043b\u0430\u0434\u0430: {_clean_text(spread.title)}\n"
            f"\u0422\u0438\u043f \u0440\u0430\u0441\u043a\u043b\u0430\u0434\u0430: {spread.slug}\n"
            f"\u0412\u043e\u043f\u0440\u043e\u0441 \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044f: {question_text}\n\n"
            f"\u041a\u0430\u0440\u0442\u044b:\n{chr(10).join(card_blocks)}\n\n"
            "\u041e\u0442\u0432\u0435\u0442 \u0434\u043e\u043b\u0436\u0435\u043d \u0431\u044b\u0442\u044c \u0447\u0438\u0441\u0442\u044b\u043c \u0440\u0443\u0441\u0441\u043a\u0438\u043c \u0442\u0435\u043a\u0441\u0442\u043e\u043c \u0431\u0435\u0437 Markdown.\n"
            "\u041e\u0431\u044b\u0447\u043d\u044b\u0435 \u0437\u0430\u0433\u043e\u043b\u043e\u0432\u043a\u0438 \u0434\u043b\u044f \u0440\u0430\u0437\u0434\u0435\u043b\u043e\u0432: "
            + ", ".join(AIService._strict_response_headings())
        )

    async def _generate_with_gemini(
        self,
        spread: Spread,
        question: str,
        drawn_cards: list[DrawnCard],
    ) -> str:
        prompt = build_reading_prompt(spread, question, drawn_cards)

        def _call_gemini() -> str:
            try:
                from google import genai

                client = genai.Client(api_key=self._settings.gemini_api_key)
                response = client.models.generate_content(
                    model=self._settings.gemini_model,
                    contents=prompt,
                )
                text = getattr(response, "text", "") or ""
            except ImportError:
                import google.generativeai as legacy_genai

                legacy_genai.configure(api_key=self._settings.gemini_api_key)
                model = legacy_genai.GenerativeModel(self._settings.gemini_model)
                response = model.generate_content(prompt)
                text = getattr(response, "text", "") or ""
            if not text.strip():
                raise RuntimeError("Gemini returned an empty response")
            return text.strip()

        return clean_ai_text(await asyncio.to_thread(_call_gemini))

    def _fallback_reading(
        self,
        spread: Spread,
        question: str,
        drawn_cards: list[DrawnCard],
        user_id: int | None = None,
        reading_id: int | None = None,
    ) -> str:
        rng = random.Random(self._seed_material(spread, question, drawn_cards, user_id, reading_id))
        question_line = question.strip()

        intro_by_spread = {
            "daily_card": [
                "РЎРµРіРѕРґРЅСЏ РєР°СЂС‚Р° Р·РІСѓС‡РёС‚ РєР°Рє РєРѕСЂРѕС‚РєР°СЏ РЅР°СЃС‚СЂРѕР№РєР° РЅР° РґРµРЅСЊ: Р±РµР· СЃРїРµС€РєРё, РЅРѕ СЃ СЏСЃРЅС‹Рј Р°РєС†РµРЅС‚РѕРј.",
                "РљР°СЂС‚Р° РґРЅСЏ РїРѕРєР°Р·С‹РІР°РµС‚, РіРґРµ Р»РµРіС‡Рµ СЃРѕС…СЂР°РЅРёС‚СЊ РІРЅСѓС‚СЂРµРЅРЅСЋСЋ СЃРѕР±СЂР°РЅРЅРѕСЃС‚СЊ Рё РЅРµ СЂР°СЃРїР»РµСЃРєР°С‚СЊ СЃРёР»С‹.",
            ],
            "quick": [
                "Р‘С‹СЃС‚СЂС‹Р№ СЂР°СЃРєР»Р°Рґ РІС‹РґРµР»СЏРµС‚ РѕРґРёРЅ РїСЂР°РєС‚РёС‡РЅС‹Р№ СЃРјС‹СЃР» Рё РїРѕРјРѕРіР°РµС‚ РЅРµ СЂР°СЃРїС‹Р»СЏС‚СЊСЃСЏ.",
                "Р—РґРµСЃСЊ РІР°Р¶РµРЅ РїСЂСЏРјРѕР№ РѕС‚РІРµС‚: С‡С‚Рѕ РІРёРґРЅРѕ СЃРµР№С‡Р°СЃ Рё РєР°РєРѕР№ С€Р°Рі Р»СѓС‡С€Рµ РЅРµ РѕС‚РєР»Р°РґС‹РІР°С‚СЊ.",
            ],
            "love": [
                "Р’ СЃРµСЂРґРµС‡РЅРѕР№ С‚РµРјРµ РєР°СЂС‚С‹ РіРѕРІРѕСЂСЏС‚ РјСЏРіРєРѕ: С‡РµСЂРµР· РєРѕРЅС‚Р°РєС‚, С‡РµСЃС‚РЅРѕСЃС‚СЊ Рё Р±РµСЂРµР¶РЅС‹Рµ РіСЂР°РЅРёС†С‹.",
                "Р­С‚РѕС‚ СЂР°СЃРєР»Р°Рґ СЃРјРѕС‚СЂРёС‚ РЅР° С‡СѓРІСЃС‚РІР° Р±РµР· РЅР°Р¶РёРјР°, РѕСЃС‚Р°РІР»СЏСЏ РјРµСЃС‚Рѕ РґР»СЏ Р¶РёРІРѕРіРѕ РґРёР°Р»РѕРіР°.",
            ],
            "money": [
                "Р”РµРЅРµР¶РЅС‹Р№ СЂР°СЃРєР»Р°Рґ РїРµСЂРµРІРѕРґРёС‚ СЃРёРјРІРѕР»С‹ РІ СЏР·С‹Рє СЂРµСЃСѓСЂСЃРѕРІ, СЂРµС€РµРЅРёР№ Рё Р±Р»РёР¶Р°Р№С€РёС… РґРµР№СЃС‚РІРёР№.",
                "Р¤РёРЅР°РЅСЃРѕРІР°СЏ С‚РµРјР° СЃРµР№С‡Р°СЃ С‚СЂРµР±СѓРµС‚ С‚СЂРµР·РІРѕРіРѕ РІР·РіР»СЏРґР°: С‡С‚Рѕ СѓР¶Рµ РµСЃС‚СЊ, С‡С‚Рѕ РјРµС€Р°РµС‚ Рё РєСѓРґР° РґРІРёРіР°С‚СЊСЃСЏ РґР°Р»СЊС€Рµ.",
            ],
            "deep": [
                "Р“Р»СѓР±РѕРєРёР№ СЂР°СЃРєР»Р°Рґ СЂР°Р·РІРѕСЂР°С‡РёРІР°РµС‚ СЃРёС‚СѓР°С†РёСЋ СЃР»РѕСЏРјРё: РІРёРґРёРјРѕРµ, СЃРєСЂС‹С‚РѕРµ, РѕРїРѕСЂСѓ Рё СЃР»РµРґСѓСЋС‰РёР№ С€Р°Рі.",
                "РљР°СЂС‚С‹ Р·РґРµСЃСЊ СЂР°Р±РѕС‚Р°СЋС‚ РєР°Рє РєР°СЂС‚Р° РјРµСЃС‚РЅРѕСЃС‚Рё СЃ РЅРµСЃРєРѕР»СЊРєРёРјРё РІР°Р¶РЅС‹РјРё РѕСЂРёРµРЅС‚РёСЂР°РјРё.",
            ],
        }
        final_by_spread = {
            "daily_card": [
                "РќР° СЃРµРіРѕРґРЅСЏ СЌС‚РѕРіРѕ РґРѕСЃС‚Р°С‚РѕС‡РЅРѕ: РґРµСЂР¶РёС‚Рµ С„РѕРєСѓСЃ РјР°Р»РµРЅСЊРєРёРј, Р° РІС‹Р±РѕСЂ С‡РµСЃС‚РЅС‹Рј.",
                "РџСѓСЃС‚СЊ РґРµРЅСЊ РїСЂРѕР№РґРµС‚ С‡РµСЂРµР· РѕРґРёРЅ СЏСЃРЅС‹Р№ РѕСЂРёРµРЅС‚РёСЂ, Р±РµР· РЅРµРѕР±С…РѕРґРёРјРѕСЃС‚Рё СЂРµС€Р°С‚СЊ РІСЃРµ СЃСЂР°Р·Сѓ.",
            ],
            "quick": [
                "РћС‚РІРµС‚ Р»СѓС‡С€Рµ РїСЂРѕРІРµСЂРёС‚СЊ РґРµР»РѕРј: РѕРґРёРЅ РєРѕРЅРєСЂРµС‚РЅС‹Р№ С€Р°Рі РїРѕРєР°Р¶РµС‚ Р±РѕР»СЊС€Рµ, С‡РµРј РґРѕР»РіРёРµ СЃРѕРјРЅРµРЅРёСЏ.",
                "РЎРµР№С‡Р°СЃ РїРѕР»РµР·РЅР° РїСЂРѕСЃС‚РѕС‚Р°: РјРµРЅСЊС€Рµ РІР°СЂРёР°РЅС‚РѕРІ, Р±РѕР»СЊС€Рµ Р°РєРєСѓСЂР°С‚РЅРѕРіРѕ РґРµР№СЃС‚РІРёСЏ.",
            ],
            "love": [
                "Р’ РѕС‚РЅРѕС€РµРЅРёСЏС… РїРѕРјРѕР¶РµС‚ СЃРїРѕРєРѕР№РЅС‹Р№ С‚РѕРЅ: РіРѕРІРѕСЂРёС‚СЊ РїСЂСЏРјРѕ, РЅРѕ Р±РµР· РґР°РІР»РµРЅРёСЏ.",
                "Р‘РµСЂРµР¶РЅРѕСЃС‚СЊ Р·РґРµСЃСЊ СЃРёР»СЊРЅРµРµ РєРѕРЅС‚СЂРѕР»СЏ; РѕСЃС‚Р°РІСЊС‚Рµ РјРµСЃС‚Рѕ Рё СЃРµР±Рµ, Рё РґСЂСѓРіРѕРјСѓ С‡РµР»РѕРІРµРєСѓ.",
            ],
            "money": [
                "Р’ СЂРµСЃСѓСЂСЃР°С… РІС‹РёРіСЂС‹РІР°РµС‚ РЅРµ СЂС‹РІРѕРє, Р° РїРѕРЅСЏС‚РЅС‹Р№ РїР»Р°РЅ Рё РІРЅРёРјР°РЅРёРµ Рє РґРµС‚Р°Р»СЏРј.",
                "РЎРѕС…СЂР°РЅРёС‚Рµ РїСЂР°РєС‚РёС‡РЅРѕСЃС‚СЊ: СЃРЅР°С‡Р°Р»Р° РѕРїРѕСЂР°, Р·Р°С‚РµРј СЂРµС€РµРЅРёРµ, РїРѕС‚РѕРј РґРІРёР¶РµРЅРёРµ.",
            ],
            "deep": [
                "РќРµ СЃР¶РёРјР°Р№С‚Рµ СЂР°СЃРєР»Р°Рґ РґРѕ РѕРґРЅРѕРіРѕ РІС‹РІРѕРґР°: Р·РґРµСЃСЊ РІР°Р¶РЅР° РїРѕСЃР»РµРґРѕРІР°С‚РµР»СЊРЅРѕСЃС‚СЊ РјР°Р»РµРЅСЊРєРёС… РїСЂРѕСЏСЃРЅРµРЅРёР№.",
                "Р“Р»Р°РІРЅР°СЏ РїРѕР»СЊР·Р° СЂР°СЃРєР»Р°РґР° РІ С‚РѕРј, С‡С‚РѕР±С‹ СѓРІРёРґРµС‚СЊ, РіРґРµ РјРѕР¶РЅРѕ РІРµСЂРЅСѓС‚СЊ СЃРµР±Рµ СѓРїСЂР°РІР»РµРЅРёРµ Р±РµР· Р¶РµСЃС‚РєРѕСЃС‚Рё.",
            ],
        }

        lines = [rng.choice(intro_by_spread.get(spread.slug, intro_by_spread["quick"]))]
        if question_line:
            lines.append(f"Р’РѕРїСЂРѕСЃ: {question_line}")
        lines.append("")

        for drawn in drawn_cards:
            position = _clean_text(drawn.position)
            title = _clean_text(drawn.card.title)
            archetype = _clean_text(drawn.card.archetype)
            light = _clean_text(drawn.card.light)
            shadow = _clean_text(drawn.card.shadow)
            symbol = _clean_text(drawn.card.symbol)
            lines.append(f"{position}: {title} СЂР°СЃРєСЂС‹РІР°РµС‚ Р°СЂС…РµС‚РёРї В«{archetype}В».")
            lines.append(f"РЎРІРµС‚ РєР°СЂС‚С‹ вЂ” {light}; СЃРёРјРІРѕР» В«{symbol}В» РїРѕРјРѕРіР°РµС‚ СѓРІРёРґРµС‚СЊ С‚РѕС‡РєСѓ РѕРїРѕСЂС‹.")
            lines.append(f"РўРµРЅРµРІР°СЏ РїРѕРґСЃРєР°Р·РєР° вЂ” {shadow}. Р•Рµ Р»СѓС‡С€Рµ Р·Р°РјРµС‚РёС‚СЊ Р·Р°СЂР°РЅРµРµ, С‡С‚РѕР±С‹ РґРµР№СЃС‚РІРѕРІР°С‚СЊ СЃРїРѕРєРѕР№РЅРµРµ.")
            lines.append("")

        lines.append(rng.choice(final_by_spread.get(spread.slug, final_by_spread["quick"])))
        return clean_ai_text("\n".join(lines).strip())

    @staticmethod
    def _seed_material(
        spread: Spread,
        question: str,
        drawn_cards: list[DrawnCard],
        user_id: int | None,
        reading_id: int | None,
    ) -> str:
        cards_part = "|".join(f"{drawn.position}:{drawn.card.slug}:{drawn.card.title}" for drawn in drawn_cards)
        time_part = datetime.now(timezone.utc).isoformat(timespec="seconds")
        return "|".join(
            [
                str(user_id or "anonymous"),
                str(reading_id or time_part),
                spread.slug,
                spread.title,
                question.strip(),
                cards_part,
            ]
        )


