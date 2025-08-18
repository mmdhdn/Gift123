"""Periodic discovery of new gifts."""
from __future__ import annotations

import asyncio
import logging
from typing import Callable, Iterable, Set

from .models import Gift, FilterBlock
from .filters import gift_matches
from .mtproto import MTProtoClient

logger = logging.getLogger(__name__)


class GiftScanner:
    def __init__(
        self,
        api: MTProtoClient,
        interval: int,
        filters: Iterable[FilterBlock],
        on_gift: Callable[[Gift], asyncio.Future | None],
    ) -> None:
        self.api = api
        self.interval = interval
        self.filters = list(filters)
        self.on_gift = on_gift
        self._seen: Set[int] = set()
        self._task: asyncio.Task | None = None
        self._stopped = asyncio.Event()

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._stopped.clear()
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._stopped.set()
        if self._task:
            await self._task

    async def _run(self) -> None:
        logger.info("scanner started")
        while not self._stopped.is_set():
            try:
                gifts_raw = await self.api.list_gifts()
                gifts = [Gift(**g) for g in gifts_raw]
                for gift in gifts:
                    if gift.id in self._seen:
                        continue
                    self._seen.add(gift.id)
                    if gift_matches(gift, self.filters):
                        logger.debug("gift matched: %s", gift)
                        res = self.on_gift(gift)
                        if asyncio.isfuture(res):
                            await res
            except Exception as e:  # pragma: no cover - network errors
                logger.warning("scanner error: %s", e)
            await asyncio.sleep(self.interval)
        logger.info("scanner stopped")
