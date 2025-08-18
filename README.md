# Telegram Gift Buyer

High performance Telegram userbot that scans and buys gifts (Stars) automatically. Built with Python 3.11+, asyncio and Pyrogram.

## Features
- Multi account support
- Configurable filters (price, supply, gift type)
- Async scanning and purchasing
- Simulation mode for safe testing
- Structured logging and optional Telegram notifications
- Typer based CLI

## Setup
1. Copy `.env.example` to `.env` and fill `API_ID` and `API_HASH` from [my.telegram.org](https://my.telegram.org).
2. Copy `config.example.toml` to `config.toml` and adjust filters and accounts.
3. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
4. Login accounts:
   ```bash
   python -m tg_gift_buyer.cli login --account acc1
   ```
5. Start the bot:
   ```bash
   python -m tg_gift_buyer.cli start-bot
   ```

## Development
Run tests with `pytest`.

## Docker
A simple Dockerfile is included for running the bot in a container.
