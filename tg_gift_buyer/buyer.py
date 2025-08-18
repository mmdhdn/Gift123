"""Purchase orchestration."""
from __future__ import annotations

import asyncio
import logging
from typing import Iterable

from .models import Gift, PurchaseResult
from .mtproto import MTProtoClient

logger = logging.getLogger(__name__)


class GiftBuyer:
    def __init__(
        self,
        api: MTProtoClient,
        recipients: Iterable[str],
        simulation: bool = False,
    ) -> None:
        self.api = api
        self.recipients = list(recipients)
        self.simulation = simulation
        self._lock = asyncio.Lock()

    async def buy(self, gift: Gift, amount: int) -> PurchaseResult:
        """Buy the gift for all recipients sequentially."""
        async with self._lock:
            for recipient in self.recipients:
                try:
                    if self.simulation:
                        logger.info("[SIMULATION] Would buy %s for %s", gift.id, recipient)
                        continue
                    await self.api.buy_gift(gift.id, amount, recipient)
                    logger.info("Bought gift %s for %s", gift.id, recipient)
                except Exception as e:  # pragma: no cover - network error
                    logger.error("Failed to buy gift %s for %s: %s", gift.id, recipient, e)
                    return PurchaseResult(gift_id=gift.id, amount=amount, recipient=recipient, success=False, message=str(e))
        return PurchaseResult(gift_id=gift.id, amount=amount, recipient=",".join(self.recipients), success=True, message="ok")
