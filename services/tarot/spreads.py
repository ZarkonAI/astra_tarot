from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Spread:
    slug: str
    title: str
    cards_count: int
    positions: tuple[str, ...]
    is_daily: bool = False


SPREADS: dict[str, Spread] = {
    "daily_card": Spread("daily_card", "Карта дня", 1, ("Карта дня",), is_daily=True),
    "quick": Spread("quick", "Быстрый расклад", 1, ("Главная подсказка",)),
    "love": Spread(
        "love",
        "Сердечный расклад",
        3,
        ("Что чувствуется сейчас", "Что важно понять", "Бережный шаг"),
    ),
    "money": Spread(
        "money",
        "Денежный путь",
        3,
        ("Текущий ресурс", "Возможность", "Осторожный шаг"),
    ),
    "deep": Spread(
        "deep",
        "Глубокий расклад",
        5,
        ("Суть ситуации", "Скрытый фактор", "Что помогает", "Что мешает", "Следующий шаг"),
    ),
}


FULL_SPREAD_SLUGS = {"quick", "love", "money", "deep"}


def get_spread(slug: str) -> Spread | None:
    return SPREADS.get(slug)
