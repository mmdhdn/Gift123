"""Data models used across the application."""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class Gift(BaseModel):
    id: int
    title: str
    price: int
    supply: int | None = None
    remaining: int | None = None
    gift_type: str = "limited"
    published_by: Optional[str] = None


class PurchaseResult(BaseModel):
    gift_id: int
    amount: int
    recipient: str
    success: bool
    message: str


class FilterBlock(BaseModel):
    min_price: int = 0
    max_price: int | float = float("inf")
    min_supply: int = 0
    max_supply: int | float = float("inf")
    amount: int = 1
    published_by: List[str] = Field(default_factory=list)
    gift_types: List[str] = Field(default_factory=lambda: ["limited", "unlimited", "premium"])

    def matches(self, gift: Gift) -> bool:
        if gift.price < self.min_price or gift.price > self.max_price:
            return False
        if gift.supply is not None:
            if gift.supply < self.min_supply:
                return False
            if isinstance(self.max_supply, (int, float)) and gift.supply > self.max_supply:
                return False
        if self.published_by and gift.published_by not in self.published_by:
            return False
        if self.gift_types and gift.gift_type not in self.gift_types:
            return False
        return True


__all__ = ["Gift", "FilterBlock", "PurchaseResult"]
