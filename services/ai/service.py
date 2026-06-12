from __future__ import annotations

import asyncio
import logging

from bot.config import Settings
from bot.texts import READING_DISCLAIMER
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
            import google.generativeai as genai

            genai.configure(api_key=self._settings.gemini_api_key)
            model = genai.GenerativeModel(self._settings.gemini_model)
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
        cards_lines = "\n".join(
            f"- {card.position}: {card.card.title}. {card.card.light}. Теневая подсказка: {card.card.shadow}."
            for card in drawn_cards
        )
        question_line = question.strip() or "Сейчас важнее прислушаться к общему настроению расклада."

        extra_notice = ""
        if spread.slug == "money":
            extra_notice = "\n\nЭто не финансовая рекомендация; используйте расклад как повод для спокойной рефлексии."
        elif spread.slug == "love":
            extra_notice = "\n\nВ отношениях выбирайте бережность, доверие к себе и уважение границ другого человека."

        return (
            "1. Общая энергия расклада\n"
            f"{spread.title} показывает тему: {question_line}\n\n"
            "2. Карты\n"
            f"{cards_lines}\n\n"
            "3. Совет звезды-проводника\n"
            "Сделайте один небольшой шаг, который возвращает ясность и внутреннюю опору.\n\n"
            "4. Важное напоминание\n"
            f"{READING_DISCLAIMER}{extra_notice}"
        )
