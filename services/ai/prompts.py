from __future__ import annotations

from services.readings.engine import DrawnCard
from services.tarot.spreads import Spread


def build_reading_prompt(spread: Spread, question: str, drawn_cards: list[DrawnCard]) -> str:
    cards_text = "\n".join(card.to_prompt_text() for card in drawn_cards)
    question_text = question.strip() or "Пользователь не указал отдельный вопрос."
    money_notice = (
        "\nДля денежного расклада пишите спокойно и практично, без обещаний результата."
        if spread.slug == "money"
        else ""
    )
    love_notice = (
        "\nДля расклада об отношениях не провоцируйте зависимость, ревность или контроль."
        if spread.slug == "love"
        else ""
    )

    return f"""
Вы - бережный русскоязычный проводник сервиса Astra Tarot.
Обращайтесь к пользователю на "вы". Тон мягкий, мистический, спокойный.
Не используйте фатализм, запугивание, манипуляции и обещания точных событий.
Пишите живо, не повторяйте шаблонные фразы и одинаковые абзацы.
Учитывайте конкретную карту, позицию и вопрос пользователя.{money_notice}{love_notice}

Расклад: {spread.title}
Вопрос: {question_text}
Карты:
{cards_text}

Дайте ответ строго по структуре:
1. Общая энергия расклада
2. Карты
3. Совет звезды-проводника
""".strip()
