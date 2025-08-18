# Telegram Gift Buyer

High-performance Telegram userbot that scans and buys Gifts (Stars) using **Telethon** and the latest **MTProto** methods. Runs on **Python 3.11+** with asyncio.

## Features
- Real payments flow: `payments.GetStarGiftsRequest` → `payments.GetPaymentFormRequest` → `payments.SendStarsFormRequest`
- Multi-account support
- Configurable filters (price, supply, gift type)
- Async scanning and auto-purchase
- Simulation mode (safe testing / dry run)
- Structured logging and optional Telegram notifications
- Typer-based CLI
- Minimal runner for multi-recipient purchases

## Setup
1. Copy `.env.example` to `.env` and fill `API_ID` and `API_HASH` from [my.telegram.org](https://my.telegram.org).
2. Copy `config.example.toml` to `config.toml` and adjust filters and accounts.
3. Install requirements:
   ```bash
   pip install -r requirements.txt
