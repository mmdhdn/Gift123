"""Misc utilities."""
from __future__ import annotations

import asyncio
from contextlib import suppress


async def cancel_and_wait(task: asyncio.Task | None) -> None:
    if task is None:
        return
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task
