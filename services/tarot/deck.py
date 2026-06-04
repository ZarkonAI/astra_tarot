from __future__ import annotations

import random
from copy import deepcopy
from services.tarot.cards import MAJOR_ARCANA


def draw_cards(count: int) -> list[dict]:
    if count > len(MAJOR_ARCANA):
        raise ValueError("Not enough cards in deck")
    cards = deepcopy(random.sample(MAJOR_ARCANA, count))
    for card in cards:
        card["is_reversed"] = False
    return cards
