"""Session management and login utilities."""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Dict

try:
    from pyrogram import Client
except Exception:  # pragma: no cover
    Client = object  # type: ignore

logger = logging.getLogger(__name__)


class AccountManager:
    def __init__(self, workdir: Path) -> None:
        self.workdir = workdir
        self.clients: Dict[str, Client] = {}

    def get_session_path(self, name: str) -> Path:
        return self.workdir / f"{name}.session"

    async def login(self, name: str, api_id: int, api_hash: str, phone: str | None = None) -> Client:
        session_name = self.get_session_path(name)
        client = Client(session_name.stem, api_id, api_hash, workdir=str(self.workdir))  # type: ignore[arg-type]
        await client.connect()
        if phone:
            sent = await client.send_code(phone)
            code = input("Enter login code: ")
            await client.sign_in(phone, code, phone_code_hash=sent.phone_code_hash)  # type: ignore[attr-defined]
        self.clients[name] = client
        logger.info("Logged in account %s", name)
        return client

    async def stop_all(self) -> None:
        for client in self.clients.values():
            try:
                await client.stop()
            except Exception:  # pragma: no cover
                pass
