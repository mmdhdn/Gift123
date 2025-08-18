"""Send logs and events to Telegram."""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

try:
    from pyrogram import Client
except Exception:  # pragma: no cover
    Client = object  # type: ignore

logger = logging.getLogger(__name__)


class Notifier:
    def __init__(self, client: Client, channel: Optional[str]) -> None:  # type: ignore[valid-type]
        self.client = client
        self.channel = channel

    async def send(self, text: str) -> None:
        if not self.channel:
            logger.debug("Notifier disabled: %s", text)
            return
        try:
            await self.client.send_message(self.channel, text)
        except Exception as e:  # pragma: no cover
            logger.warning("Failed to send notification: %s", e)
