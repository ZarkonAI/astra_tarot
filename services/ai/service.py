from __future__ import annotations

import asyncio
import logging

from bot.config import Settings
from services.ai.prompts import build_reading_prompt
from services.readings.engine import DrawnCard
from services.tarot.spreads import Spread


logger = logging.getLogger(__name__)


class AIService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def generate_reading(
        self,
        spread: Spread,
        question: str,
        drawn_cards: list[DrawnCard],
    ) -> str:
        if self._settings.ai_provider == "gemini" and self._settings.gemini_api_key:
            try:
                return await self._generate_with_gemini(spread, question, drawn_cards)
            except Exception:
                logger.exception("Gemini request failed; falling back to local interpretation.")

        return self._fallback_reading(spread, question, drawn_cards)

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
    ) -> str:
        question_line = question.strip()
        cards_lines = "\n".join(self._card_line(card) for card in drawn_cards)
        intro_by_spread = {
            "daily_card": "Сегодняшняя карта подсвечивает тон дня без лишнего шума.",
            "quick": "Быстрый расклад собирает главный смысл в один ясный акцент.",
            "love": "Сердечный расклад говорит мягко: здесь важны тон, чувство и честность с собой.",
            "money": "Денежный путь смотрит на ресурс, возможность и практичный следующий шаг.",
            "deep": "Глубокий расклад разворачивает ситуацию слоями: видимое, скрытое и то, что помогает двигаться дальше.",
        }
        advice_by_spread = {
            "daily_card": "Возьмите из карты одно слово и проверьте, где оно отзывается в течение дня.",
            "quick": "Сфокусируйтесь на ближайшем действии, которое можно сделать без драматизации.",
            "love": "Выберите бережную формулировку для себя или другого человека и не спешите с выводом.",
            "money": "Отделите реальный ресурс от тревожного ожидания и наметьте один спокойный шаг.",
            "deep": "Запишите, что поддерживает вас сейчас, и что стоит мягко отпустить.",
        }
        question_part = f"\nВопрос: {question_line}\n" if question_line else ""

        return (
            "1. Общая энергия расклада\n"
            f"{intro_by_spread.get(spread.slug, 'Карты собирают несколько важных символов в один образ.')}"
            f"{question_part}\n\n"
            "2. Карты\n"
            f"{cards_lines}\n\n"
            "3. Совет звезды-проводника\n"
            f"{advice_by_spread.get(spread.slug, 'Выберите один честный и спокойный следующий шаг.')}"
        )

    @staticmethod
    def _card_line(drawn_card: DrawnCard) -> str:
        return (
            f"- {drawn_card.position}: {drawn_card.card.title}. "
            f"Свет карты: {drawn_card.card.light}. "
            f"Тень, которую стоит заметить: {drawn_card.card.shadow}."
        )
