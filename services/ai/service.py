from __future__ import annotations

import asyncio
import logging
import random
from datetime import datetime, timezone

from bot.config import Settings
from services.ai.prompts import build_reading_prompt
from services.readings.engine import DrawnCard
from services.tarot.spreads import Spread


logger = logging.getLogger(__name__)


def _short_error(exc: Exception) -> str:
    message = str(exc).strip() or exc.__class__.__name__
    message = message.replace("\n", " ").replace("\r", " ")
    return message[:240]


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
        if self._settings.ai_provider == "local":
            if not self._local_provider_logged:
                logger.warning("AI provider is local; Gemini calls are disabled.")
                self._local_provider_logged = True
            return self._fallback_reading(spread, question, drawn_cards, user_id=user_id, reading_id=reading_id)

        if self._settings.ai_provider == "gemini" and self._settings.gemini_api_key:
            try:
                return await self._generate_with_gemini(spread, question, drawn_cards)
            except Exception as exc:
                logger.warning("Gemini request failed; using fallback. Reason: %s", _short_error(exc))
                logger.debug("Gemini request traceback", exc_info=True)

        return self._fallback_reading(spread, question, drawn_cards, user_id=user_id, reading_id=reading_id)

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
