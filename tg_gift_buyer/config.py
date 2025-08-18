"""Configuration loading and validation using Pydantic."""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional
import tomllib
from pydantic import BaseModel, Field, PositiveInt


class FilterConfig(BaseModel):
    min_price: int = 0
    max_price: int | float = Field(default=float("inf"))
    min_supply: int = 0
    max_supply: int | float = Field(default=float("inf"))
    amount: PositiveInt = 1
    published_by: List[str] = Field(default_factory=list)
    gift_types: List[str] = Field(default_factory=lambda: ["limited", "unlimited", "premium"])


class AccountConfig(BaseModel):
    name: str
    phone: Optional[str] = None
    scan_interval_secs: PositiveInt = 2
    spend_cap_stars: int = 0
    recipients: List[str] = Field(default_factory=list)
    filters: Optional[FilterConfig] = None


class Config(BaseModel):
    poll_interval_secs: PositiveInt = 2
    simulation: bool = False
    log_level: str = "INFO"
    log_telegram_channel: Optional[str] = None
    defaults: FilterConfig = Field(default_factory=FilterConfig)
    accounts: List[AccountConfig] = Field(default_factory=list)

    @classmethod
    def load(cls, path: Path) -> "Config":
        data = tomllib.loads(path.read_text())
        return cls.model_validate(data)


__all__ = ["Config", "FilterConfig", "AccountConfig"]
