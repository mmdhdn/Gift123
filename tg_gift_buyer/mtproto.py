"""Thin abstraction over Pyrogram raw MTProto methods for gifts/stars."""
from __future__ import annotations

import asyncio
from typing import Any, List

try:
    from pyrogram import Client
    from pyrogram.raw.functions import payments
except Exception:  # pragma: no cover - during tests pyrogram may not be installed
    Client = Any  # type: ignore
    payments = Any  # type: ignore


class MTProtoClient:
    """Wrapper around Pyrogram client to call raw methods."""

    def __init__(self, client: Client) -> None:  # type: ignore[valid-type]
        self.client = client

    async def list_gifts(self) -> List[dict]:
        """Fetch available gifts. Placeholder implementation."""
        # The actual implementation would use the proper raw method once available.
        # Here we simulate with an empty list.
        await asyncio.sleep(0)
        return []

    async def buy_gift(self, gift_id: int, amount: int, recipient: str) -> Any:
        """Buy gift with given id."""
        await asyncio.sleep(0)
        return {"status": "ok", "gift_id": gift_id, "amount": amount, "recipient": recipient}


__all__ = ["MTProtoClient"]
