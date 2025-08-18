"""Filtering utilities."""
from __future__ import annotations

from typing import Iterable
from .models import Gift, FilterBlock


def gift_matches(gift: Gift, filters: Iterable[FilterBlock]) -> bool:
    """Return True if gift matches any of the filter blocks."""
    for block in filters:
        if block.matches(gift):
            return True
    return False


__all__ = ["gift_matches"]
