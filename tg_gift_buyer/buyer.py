"""Purchase orchestration."""
from __future__ import annotations

import asyncio
import logging
from typing import Iterable

from .models import StarGiftModel, PurchaseResult
from . import mtproto

logger = logging.getLogger(__name__)


class GiftBuyer:
    def __init__(
        self,
        client,
        recipients: Iterable[str],
        simulation: bool = False,
    ) -> None:
        self.client = client
        self.recipients = list(recipients)
        self.simulation = simulation
        self._lock = asyncio.Lock()

    async def buy(self, gift: StarGiftModel, amount: int) -> PurchaseResult:
        """Buy the gift for all recipients sequentially."""
        async with self._lock:
            for recipient in self.recipients:
                try:
                    if self.simulation:
                        logger.info("[SIMULATION] Would buy %s for %s", gift.id, recipient)
                        continue
                    user = await mtproto.resolve_user(self.client, recipient)
                    await mtproto.buy_star_gift(self.client, user, gift.id)
                    logger.info("Bought gift %s for %s", gift.id, recipient)
                except Exception as e:  # pragma: no cover - network error
                    logger.error("Failed to buy gift %s for %s: %s", gift.id, recipient, e)
                    return PurchaseResult(gift_id=gift.id, recipient=recipient, success=False, message=str(e))
        return PurchaseResult(gift_id=gift.id, recipient=",".join(self.recipients), success=True, message="ok")
