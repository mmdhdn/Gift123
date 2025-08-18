"""Command line interface for tg_gift_buyer."""
from __future__ import annotations

import asyncio
from pathlib import Path
import os

import typer
from dotenv import load_dotenv

from .app import start, stop
from .accounts import AccountManager
from .config import Config

app = typer.Typer(help="Telegram Gift Buyer")


@app.command()
def init(path: Path = typer.Option(Path("."))):
    """Generate example config and env files."""
    (path / ".env.example").write_text("API_ID=12345\nAPI_HASH=0123456789abcdef\n")
    (path / "config.example.toml").write_text("poll_interval_secs=2\n")
    typer.echo("Generated .env.example and config.example.toml")


@app.command()
def login(account: str, config_path: Path = typer.Option("config.toml")):
    """Interactive login for an account."""
    load_dotenv()
    api_id = int(os.environ["API_ID"])
    api_hash = os.environ["API_HASH"]
    cfg = Config.load(config_path)
    acc = next((a for a in cfg.accounts if a.name == account), None)
    if not acc:
        raise typer.Exit(f"Account {account} not found in config")
    manager = AccountManager(Path("sessions"))
    asyncio.run(manager.login(acc.name, api_id, api_hash, acc.phone))


@app.command()
def start_bot(config_path: Path = typer.Option("config.toml")):
    """Start scanners for all accounts."""
    load_dotenv()
    api_id = int(os.environ["API_ID"])
    api_hash = os.environ["API_HASH"]

    async def _run():
        scanners = await start(config_path, api_id, api_hash)
        try:
            await asyncio.Event().wait()
        finally:
            await stop(scanners)

    asyncio.run(_run())


def main():  # pragma: no cover - entry point
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
