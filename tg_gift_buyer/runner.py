"""Simple orchestrator that scans and buys star gifts."""
from __future__ import annotations

import asyncio
import logging
from typing import Sequence

from . import mtproto
from .filters import gift_matches
from .models import StarGiftModel, GiftFilter

logger = logging.getLogger(__name__)


async def run_monitor(
    client,
    recipients: Sequence[str],
    filters: Sequence[GiftFilter],
    poll_interval: int = 2,
    simulation: bool = False,
    iterations: int | None = None,
) -> None:
    last_hash = 0
    seen_ids: set[int] = set()
    count = 0
    while iterations is None or count < iterations:
        count += 1
        try:
            last_hash, gifts = await mtproto.list_gifts(client, last_hash)
            for g in gifts:
                gid = getattr(g, "id")
                if gid in seen_ids:
                    continue
                seen_ids.add(gid)
                model = StarGiftModel.from_telethon(g)
                if gift_matches(model, filters):
                    for rcpt in recipients:
                        if simulation:
                            logger.info("[SIMULATION] Would buy gift %s for %s", model.id, rcpt)
                        else:
                            user = await mtproto.resolve_user(client, rcpt)
                            await mtproto.buy_star_gift(client, user, model.id)
        except Exception as e:  # pragma: no cover - network or other errors
            logger.error("monitor error: %s", e)
        if iterations is None or count < iterations:
            await asyncio.sleep(poll_interval)


__all__ = ["run_monitor"]
