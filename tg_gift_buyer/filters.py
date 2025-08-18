"""Filtering utilities for star gifts."""
from __future__ import annotations

from typing import Iterable

from .models import StarGiftModel, GiftFilter


def _matches(gift: StarGiftModel, flt: GiftFilter) -> bool:
    if gift.sold_out:
        return False
    if gift.stars < flt.min_price or gift.stars > flt.max_price:
        return False
    if flt.gift_types and gift.type not in flt.gift_types:
        return False
    if gift.limited:
        remain = gift.availability_remains or 0
        if remain < flt.min_supply:
            return False
        if isinstance(flt.max_supply, (int, float)) and remain > flt.max_supply:
            return False
    return True


def gift_matches(gift: StarGiftModel, filters: Iterable[GiftFilter]) -> bool:
    return any(_matches(gift, f) for f in filters)


__all__ = ["gift_matches"]
