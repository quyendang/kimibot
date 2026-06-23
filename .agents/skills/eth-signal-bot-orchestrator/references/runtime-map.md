# ETH Signal Bot Runtime Map

## Entry Points

- `main.py`: starts health server, sends startup Telegram notification, then enters the scheduler loop.
- `Procfile`: Railway worker command, currently `python main.py`.
- `eth_signal_bot/health/server.py`: simple HTTP server for `/` and `/health`.

## Core Modules

- `eth_signal_bot/core/config.py`: environment-backed runtime settings.
- `eth_signal_bot/core/scheduler.py`: continuous analyze/sleep loop and summary cadence.
- `eth_signal_bot/exchanges/binance.py`: Binance REST helpers for klines and current price.
- `eth_signal_bot/indicators/technicals.py`: RSI, EMA, MA, MACD calculations.
- `eth_signal_bot/indicators/signals.py`: signal scoring and explanation text.
- `eth_signal_bot/notifiers/telegram.py`: Telegram HTML payloads, escaping, retries, and startup/summary messages.

## Risk Areas

- Infinite loop behavior and sleep intervals.
- Live external calls to Binance and Telegram.
- Telegram HTML parsing and escaping.
- Environment parsing for numeric lists and thresholds.
- Alert spam when thresholds are too sensitive.
- Missing tests around indicator edge cases and message formatting.

## Verification Notes

- Prefer mocked requests for exchange and Telegram behavior.
- Use deterministic pandas Series/DataFrames for indicator and scoring tests.
- For health checks, use a temporary port in local verification.
- Avoid sending live Telegram messages unless explicitly requested.
