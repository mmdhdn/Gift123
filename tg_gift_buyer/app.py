"""Application bootstrap and lifecycle management."""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import List

from .config import Config
from .models import FilterBlock
from .scanner import GiftScanner
from .buyer import GiftBuyer
from .mtproto import MTProtoClient
from .accounts import AccountManager
from .logging_setup import setup_logging

logger = logging.getLogger(__name__)


async def start(config_path: Path, api_id: int, api_hash: str) -> List[GiftScanner]:
    config = Config.load(config_path)
    setup_logging(config.log_level)
    manager = AccountManager(Path("sessions"))
    scanners: List[GiftScanner] = []
    for acc_cfg in config.accounts:
        client = await manager.login(acc_cfg.name, api_id, api_hash, acc_cfg.phone)
        mt = MTProtoClient(client)
        filt_cfg = acc_cfg.filters or config.defaults
        filter_block = FilterBlock(**filt_cfg.model_dump())
        buyer = GiftBuyer(mt, acc_cfg.recipients, simulation=config.simulation)
        scanner = GiftScanner(
            mt,
            acc_cfg.scan_interval_secs,
            [filter_block],
            lambda gift, b=buyer, fb=filter_block: b.buy(gift, fb.amount),
        )
        await scanner.start()
        scanners.append(scanner)
    logger.info("All scanners started")
    return scanners


async def stop(scanners: List[GiftScanner]) -> None:
    await asyncio.gather(*(s.stop() for s in scanners))
