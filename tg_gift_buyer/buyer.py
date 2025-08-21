"""Purchase orchestration."""
from __future__ import annotations

import asyncio
import logging
from typing import Iterable

from .models import StarGiftModel, PurchaseResult
from . import mtproto
from .mtproto import errors

logger = logging.getLogger(__name__)


class GiftBuyer:
    def __init__(
        self,
        client,
        recipients: Iterable[str],
        simulation: bool = False,
        skip_on_low_balance: bool = True,
    ) -> None:
        self.client = client
        self.recipients = list(recipients)
        self.simulation = simulation
        self.skip_on_low_balance = skip_on_low_balance
        self._lock = asyncio.Lock()
        # Best-effort cache of the last known balance.  In real usage it can be
        # updated from external signals.  Tests may set it directly.
        self._balance_cache: int | None = None

    async def get_balance_snapshot(self) -> int | None:
        """Return cached balance value if available."""
        return self._balance_cache

    async def buy(self, gift: StarGiftModel, amount: int) -> PurchaseResult:
        """Buy the gift for all recipients sequentially."""
        async with self._lock:
            price = gift.stars * amount
            balance = await self.get_balance_snapshot()
            account_session = getattr(self.client, "session_name", None)
            if (
                self.skip_on_low_balance
                and balance is not None
                and price > balance
            ):
                logger.info(
                    "SKIP_BALANCE gift_id=%s price=%s balance_snapshot=%s account_session=%s reason=precheck",
                    gift.id,
                    price,
                    balance,
                    account_session,
                )
                return PurchaseResult(
                    gift_id=gift.id,
                    recipient=",".join(self.recipients),
                    success=False,
                    message="skipped_low_balance",
                )

            for recipient in self.recipients:
                try:
                    if self.simulation:
                        logger.info("[SIMULATION] Would buy %s for %s", gift.id, recipient)
                        continue
                    user = await mtproto.resolve_user(self.client, recipient)
                    await mtproto.buy_star_gift(self.client, user, gift.id)
                    logger.info("Bought gift %s for %s", gift.id, recipient)
                except errors.RPCError as e:
                    es = str(e)
                    name = e.__class__.__name__
                    low_balance = "BALANCE_TOO_LOW" in es or (
                        "BALANCE" in name.upper() and "LOW" in name.upper()
                    )
                    if self.skip_on_low_balance and low_balance:
                        bal = await self.get_balance_snapshot()
                        logger.info(
                            "SKIP_BALANCE gift_id=%s price=%s balance_snapshot=%s account_session=%s reason=rpc_error",
                            gift.id,
                            price,
                            bal,
                            account_session,
                        )
                        return PurchaseResult(
                            gift_id=gift.id,
                            recipient=recipient,
                            success=False,
                            message="skipped_low_balance",
                        )
                    logger.error(
                        "Failed to buy gift %s for %s: %s", gift.id, recipient, e
                    )
                    return PurchaseResult(
                        gift_id=gift.id,
                        recipient=recipient,
                        success=False,
                        message=str(e),
                    )
                except Exception as e:  # pragma: no cover - network error
                    logger.error(
                        "Failed to buy gift %s for %s: %s", gift.id, recipient, e
                    )
                    return PurchaseResult(
                        gift_id=gift.id,
                        recipient=recipient,
                        success=False,
                        message=str(e),
                    )
        return PurchaseResult(
            gift_id=gift.id,
            recipient=",".join(self.recipients),
            success=True,
            message="ok",
        )
