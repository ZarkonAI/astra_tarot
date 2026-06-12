from __future__ import annotations

import random

from services.tarot.cards import MAJOR_ARCANA, TarotCard


_RANDOM = random.SystemRandom()


def draw_cards(count: int) -> list[TarotCard]:
    if count < 1:
        raise ValueError("count must be positive")
    if count > len(MAJOR_ARCANA):
        raise ValueError("count exceeds deck size")
    return list(_RANDOM.sample(MAJOR_ARCANA, count))
