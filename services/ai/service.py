from __future__ import annotations

import asyncio
import logging
import random
from datetime import datetime, timezone
from typing import Any

import httpx

from bot.config import Settings
from services.ai.prompts import build_reading_prompt
from services.readings.engine import DrawnCard
from services.tarot.spreads import Spread


logger = logging.getLogger(__name__)


def _short_error(exc: Exception) -> str:
    message = str(exc).strip() or exc.__class__.__name__
    message = message.replace("\n", " ").replace("\r", " ")
    return message[:240]


def _short_response_text(response: httpx.Response) -> str:
    text = response.text.strip().replace("\n", " ").replace("\r", " ")
    return text[:180] or "empty response"


class OpenRouterTimeoutError(RuntimeError):
    pass


class OpenRouterLowQualityTextError(RuntimeError):
    pass


def _extract_openrouter_content(data: dict[str, Any]) -> str:
    try:
        content = data["choices"][0]["message"].get("content", "")
    except (KeyError, IndexError, TypeError):
        return ""
    if not isinstance(content, str):
        return ""
    return content.strip()


def _is_cjk_character(char: str) -> bool:
    code = ord(char)
    return (
        0x3400 <= code <= 0x4DBF
        or 0x4E00 <= code <= 0x9FFF
        or 0x3040 <= code <= 0x30FF
        or 0xAC00 <= code <= 0xD7AF
    )


def _is_bad_ai_text(text: str) -> bool:
    normalized = (text or "").strip()
    if not normalized or len(normalized) < 80:
        return True

    lowered = normalized.lower()
    forbidden_markers = (
        "residue",
        "multiply",
        "biome",
        "arquétique",
        "arquetique",
        "нейтросфер",
        "танцет",
        "龛",
        "openrouter",
        "gemini",
        "fallback",
        "api error",
        "ошибка api",
    )
    if any(marker in lowered for marker in forbidden_markers):
        return True
    if any(_is_cjk_character(char) for char in normalized):
        return True

    cyrillic_letters = sum(1 for char in normalized if "а" <= char.lower() <= "я" or char in "Ёё")
    latin_letters = sum(1 for char in normalized if "a" <= char.lower() <= "z")
    if cyrillic_letters < 50:
        return True
    return latin_letters > cyrillic_letters * 0.08


def _openrouter_response_structure(spread_slug: str) -> str:
    structures = {
        "daily_card": "2-4 коротких абзаца без длинных списков; живой совет на день.",
        "quick": "Короткое вступление; карта или карты; смысл ситуации; совет.",
        "love": "Мягкий эмоциональный стиль; чувства, контакт и границы; бережный совет.",
        "money": "Практичный стиль; ресурсы, решения и ближайший шаг; без финансовых гарантий.",
        "deep": "Понятная структура, максимум 4-6 абзацев; каждый абзац 2-4 предложения; без длинных списков и мистического бреда; общий вывод.",
    }
    return structures.get(spread_slug, structures["quick"])


class AIService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._local_provider_logged = False

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
            except OpenRouterTimeoutError:
                logger.warning("OpenRouter timeout; using fallback.")
                logger.debug("OpenRouter timeout traceback", exc_info=True)
            except OpenRouterLowQualityTextError:
                logger.debug("OpenRouter low-quality text traceback", exc_info=True)
            except Exception as exc:
                logger.warning("OpenRouter request failed; using fallback. Reason: %s", _short_error(exc))
                logger.debug("OpenRouter request traceback", exc_info=True)
            return self._fallback_reading(spread, question, drawn_cards, user_id=user_id, reading_id=reading_id)

        if provider == "gemini":
            try:
                return await self._generate_with_gemini(spread, question, drawn_cards)
            except Exception as exc:
                logger.warning("Gemini request failed; using fallback. Reason: %s", _short_error(exc))
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

        for is_retry in (False, True):
            payload = {
                "model": self._settings.openrouter_model,
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
            data = await self._post_openrouter(payload)
            logger.info("OpenRouter model used: %s", data.get("model", self._settings.openrouter_model))

            content = _extract_openrouter_content(data)
            if not _is_bad_ai_text(content):
                return content

        logger.warning("OpenRouter returned low-quality text twice; using local fallback.")
        raise OpenRouterLowQualityTextError("OpenRouter returned low-quality text twice")

    async def _post_openrouter(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self._settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self._settings.openrouter_http_referer,
            "X-Title": self._settings.openrouter_x_title,
        }

        try:
            async with httpx.AsyncClient(timeout=self._settings.openrouter_timeout_seconds) as client:
                response = await asyncio.wait_for(
                    client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers=headers,
                        json=payload,
                    ),
                    timeout=self._settings.openrouter_timeout_seconds,
                )
        except (httpx.TimeoutException, asyncio.TimeoutError) as exc:
            raise OpenRouterTimeoutError("OpenRouter request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"OpenRouter HTTP error: {_short_error(exc)}") from exc

        if response.status_code == 401:
            raise RuntimeError("OpenRouter authentication failed")
        if response.status_code == 429:
            raise RuntimeError("OpenRouter rate limit reached")
        if response.status_code != 200:
            raise RuntimeError(f"OpenRouter status {response.status_code}: {_short_response_text(response)}")

        try:
            return response.json()
        except ValueError as exc:
            raise RuntimeError("OpenRouter returned invalid JSON") from exc

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
        return (
            "Ты — мягкий русскоязычный интерпретатор символических раскладов Astra Tarot.\n"
            "Пиши уважительно на \"вы\".\n"
            "Отвечай только на русском языке.\n"
            "Не используй английские слова, латиницу, китайские, японские или корейские символы, псевдослова и случайные символы.\n"
            "Если не уверен в формулировке, пиши проще.\n"
            "Не используй странные слова вроде residue, multiply, signs, biome, arquétique.\n"
            "Не смешивай языки.\n"
            "Не упоминай модель, API, OpenRouter, Gemini, fallback и ошибки.\n"
            "Не добавляй дисклеймеры.\n"
            "Не делай слишком поэтичный бессвязный текст.\n"
            "Пиши красиво, но понятно.\n"
            "Лучше коротко и ясно, чем длинно и мутно.\n"
            "Стиль: мистический, ясный, теплый, без запугивания и фатализма.\n"
            "Не упоминай, что ты ИИ.\n"
            "Не обещай точных событий.\n"
            "Не используй манипулятивные формулировки.\n"
            "Не повторяй шаблонные фразы.\n"
            "Дай готовую трактовку, которую можно сразу отправить пользователю."
        )

    @staticmethod
    def _openrouter_user_prompt(
        spread: Spread,
        question: str,
        drawn_cards: list[DrawnCard],
        is_retry: bool = False,
    ) -> str:
        question_text = question.strip() or "Пользователь не указал отдельный вопрос."
        cards_text = "\n".join(
            "\n".join(
                [
                    f"- Позиция: {drawn.position}",
                    f"  Карта: {drawn.card.title}",
                    f"  Светлое значение: {drawn.card.light}",
                    f"  Теневая подсказка: {drawn.card.shadow}",
                    f"  Символ: {drawn.card.symbol}",
                    f"  Архетип: {drawn.card.archetype}",
                ]
            )
            for drawn in drawn_cards
        )
        retry_text = (
            "Предыдущая попытка была отклонена, потому что текст был некачественным.\n"
            "Верните только чистый, понятный русский текст без латиницы и случайных слов.\n\n"
            if is_retry
            else ""
        )
        structure = _openrouter_response_structure(spread.slug)
        return (
            f"{retry_text}"
            f"Название расклада: {spread.title}\n"
            f"Тип расклада: {spread.slug}\n"
            f"Вопрос пользователя: {question_text}\n\n"
            f"Карты:\n{cards_text}\n\n"
            f"Желаемая структура ответа:\n{structure}"
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

        return await asyncio.to_thread(_call_gemini)

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
                "Сегодня расклад звучит как короткая настройка на день: без спешки, но с ясным акцентом.",
                "Карта дня показывает, где легче сохранить внутреннюю собранность и не расплескать силы.",
                "Главный знак на сегодня стоит читать через действие, которое можно сделать спокойно и вовремя.",
            ],
            "quick": [
                "Быстрый расклад выделяет один практичный смысл и помогает не распыляться.",
                "Здесь важен прямой ответ: что видно сейчас и какой шаг лучше не откладывать.",
                "Расклад собирает ситуацию в короткий фокус, чтобы отделить главное от фонового шума.",
            ],
            "love": [
                "В сердечной теме карты говорят мягко: через контакт, честность и бережные границы.",
                "Этот расклад смотрит на чувства без нажима, оставляя место для живого диалога.",
                "Важнее всего здесь тон общения: что согревает связь и что просит большей осторожности.",
            ],
            "money": [
                "Денежный расклад переводит символы в язык ресурсов, решений и ближайших действий.",
                "Здесь карты подсвечивают, где стоит беречь силы, а где можно действовать практичнее.",
                "Финансовая тема сейчас требует трезвого взгляда: что уже есть, что мешает и куда двигаться дальше.",
            ],
            "deep": [
                "Глубокий расклад разворачивает ситуацию слоями: видимое, скрытое, опору и следующий шаг.",
                "Карты здесь работают не как быстрый ответ, а как карта местности с несколькими важными ориентирами.",
                "Этот расклад полезен, когда нужно увидеть не только событие, но и внутреннюю механику происходящего.",
            ],
        }

        card_energy_templates = [
            "{position}: {title} раскрывает архетип «{archetype}». Свет карты — {light}; символ «{symbol}» помогает увидеть, где уже есть точка опоры.",
            "В позиции «{position}» карта {title} говорит через образ «{symbol}»: здесь заметны {light}, а архетип «{archetype}» задаёт направление.",
            "{title} на месте «{position}» показывает ресурс: {light}. Её символ — {symbol}, и он делает смысл карты более конкретным.",
            "Позиция «{position}» окрашена картой {title}: архетип «{archetype}» выводит на первый план {light}.",
        ]
        shadow_templates = [
            "Теневая сторона здесь — {shadow}; её лучше заметить заранее, чтобы не действовать на автомате.",
            "Слабое место карты связано с темой: {shadow}. Это не запрет, а сигнал выбрать более точный темп.",
            "Если ситуация начнёт буксовать, проверьте проявления тени: {shadow}.",
            "Напряжение может прийти через {shadow}; мягкая внимательность снизит риск лишней резкости.",
        ]
        advice_templates = [
            "Практичный ход: опереться на {light} и сделать один шаг, который не спорит с вашим состоянием.",
            "Совет карты — использовать ресурс «{light}» и не кормить сценарий, где включается {shadow}.",
            "Лучшее действие сейчас: выбрать форму, в которой {archetype} проявится спокойно и полезно.",
            "Пусть символ «{symbol}» станет подсказкой: действуйте проще, но не теряйте смысл.",
        ]
        final_by_spread = {
            "daily_card": [
                "На сегодня этого достаточно: держите фокус маленьким, а выбор — честным.",
                "Пусть день пройдёт через один ясный ориентир, без необходимости всё решать сразу.",
            ],
            "quick": [
                "Ответ лучше проверить делом: один конкретный шаг покажет больше, чем долгие сомнения.",
                "Сейчас полезна простота: меньше вариантов, больше аккуратного действия.",
            ],
            "love": [
                "В отношениях поможет спокойный тон: говорить прямо, но без давления.",
                "Бережность здесь сильнее контроля; оставьте место и себе, и другому человеку.",
            ],
            "money": [
                "В ресурсах выигрывает не рывок, а понятный план и внимательность к деталям.",
                "Сохраните практичность: сначала опора, затем решение, потом движение.",
            ],
            "deep": [
                "Не сжимайте расклад до одного вывода: здесь важна последовательность маленьких прояснений.",
                "Главная польза расклада — увидеть, где вы можете вернуть себе управление без жёсткости.",
            ],
        }

        lines = [rng.choice(intro_by_spread.get(spread.slug, intro_by_spread["quick"]))]
        if question_line:
            lines.append(f"Вопрос: {question_line}")
        lines.append("")

        for drawn in drawn_cards:
            card = drawn.card
            payload = {
                "position": drawn.position,
                "title": card.title,
                "archetype": card.archetype,
                "light": card.light,
                "shadow": card.shadow,
                "symbol": card.symbol,
            }
            lines.append(rng.choice(card_energy_templates).format(**payload))
            lines.append(rng.choice(shadow_templates).format(**payload))
            lines.append(rng.choice(advice_templates).format(**payload))
            lines.append("")

        lines.append(rng.choice(final_by_spread.get(spread.slug, final_by_spread["quick"])))
        return "\n".join(lines).strip()

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
