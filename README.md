# Telegram Gift Buyer

Async Telegram userbot that scans and buys Gifts (Stars) using Telethon and the latest MTProto methods. Runs on Python 3.11+.

## Features
- Real payments.GetStarGiftsRequest / SendStarsFormRequest usage
- Configurable price and supply filters
- Simulation mode for dry runs
- Minimal runner for multi-recipient purchases

## Setup
1. Copy `.env.example` to `.env` and fill `API_ID` and `API_HASH` from [my.telegram.org](https://my.telegram.org).
2. Copy `config.example.toml` to `config.toml` and adjust options.
3. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
4. Run in simulation mode:
   ```bash
   python -m tg_gift_buyer --simulation
   ```

## Testing
Run tests with `pytest -q`.
