"""Configuration loaded from environment variables."""
import os

SYMBOL = os.getenv("SYMBOL", "ETHUSDT")

TIMEFRAMES = {
    "1h": {"interval": os.getenv("TF_1H", "1h"), "limit": int(os.getenv("TF_1H_LIMIT", 200))},
    "4h": {"interval": os.getenv("TF_4H", "4h"), "limit": int(os.getenv("TF_4H_LIMIT", 150))},
    "1d": {"interval": os.getenv("TF_1D", "1d"), "limit": int(os.getenv("TF_1D_LIMIT", 120))},
}

BUY_THRESHOLD = int(os.getenv("BUY_THRESHOLD", 3))
SELL_THRESHOLD = int(os.getenv("SELL_THRESHOLD", 3))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 300))

# Price zones for ETH (comma-separated integers)
SUPPORT_ZONES = [int(x) for x in os.getenv("SUPPORT_ZONES", "1620,1590,1550").split(",") if x]
RESISTANCE_ZONES = [int(x) for x in os.getenv("RESISTANCE_ZONES", "1685,1715,1780").split(",") if x]

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Health-check server
HEALTH_HOST = os.getenv("HEALTH_HOST", "0.0.0.0")
HEALTH_PORT = int(os.getenv("PORT", os.getenv("HEALTH_PORT", 8080)))
