"""Data models for star gifts and filters."""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class StarGiftModel(BaseModel):
    id: int
    title: Optional[str] = None
    stars: int
    limited: bool
    sold_out: bool
    availability_remains: Optional[int] = None
    availability_total: Optional[int] = None
    rarity: Optional[str] = None
    premium_required: Optional[bool] = None
    type: str  # "limited" | "unlimited"

    @classmethod
    def from_telethon(cls, gift) -> "StarGiftModel":
        limited = bool(getattr(gift, "availability_total", None))
        remaining = getattr(gift, "availability_remains", None)
        sold_out = bool(limited and remaining == 0)
        return cls(
            id=getattr(gift, "id"),
            title=getattr(gift, "title", None),
            stars=getattr(gift, "stars", 0),
            limited=limited,
            sold_out=sold_out,
            availability_remains=remaining,
            availability_total=getattr(gift, "availability_total", None),
            rarity=getattr(gift, "rarity", None),
            premium_required=getattr(gift, "premium", None),
            type="limited" if limited else "unlimited",
        )


class GiftFilter(BaseModel):
    min_price: int = 0
    max_price: int | float = float("inf")
    min_supply: int = 0
    max_supply: int | float = float("inf")
    gift_types: List[str] = Field(default_factory=lambda: ["limited", "unlimited"])


class PurchaseResult(BaseModel):
    gift_id: int
    recipient: str
    success: bool
    message: str = ""


__all__ = ["StarGiftModel", "GiftFilter", "PurchaseResult"]
