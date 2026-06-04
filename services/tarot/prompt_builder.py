from __future__ import annotations

from pathlib import Path
from services.tarot.spreads import SPREADS

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"
PROMPT_FILES = {
    "daily_card": "daily_card.txt",
    "quick_reading": "quick_reading.txt",
    "heart_reading": "heart_reading.txt",
    "money_path": "money_path.txt",
    "deep_reading": "deep_reading.txt",
}


def _read_prompt(filename: str) -> str:
    return (PROMPTS_DIR / filename).read_text(encoding="utf-8")


def build_prompt(spread_type: str, question: str, cards: list[dict]) -> str:
    spread = SPREADS[spread_type]
    system_prompt = _read_prompt("system_prompt.txt")
    spread_prompt = _read_prompt(PROMPT_FILES[spread_type])
    positions = spread["positions"]

    card_lines = []
    for index, card in enumerate(cards):
        position = positions[index] if index < len(positions) else f"Карта {index + 1}"
        card_lines.append(
            f"{index + 1}. Позиция: {position}\n"
            f"   Карта: {card['name']}\n"
            f"   Ключевые слова: {card['keywords']}\n"
            f"   Базовое значение: {card['meaning']}"
        )
    cards_text = "\n\n".join(card_lines)

    return f"""
{system_prompt}

Тип расклада: {spread['title']}
Вопрос пользователя: {question}

Выпавшие карты:
{cards_text}

Инструкция для конкретного расклада:
{spread_prompt}
""".strip()
