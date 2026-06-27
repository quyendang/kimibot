"""USDT market-cap percentage monitor."""
from dataclasses import dataclass
from datetime import datetime

from eth_signal_bot.core import config
from eth_signal_bot.exchanges.coingecko import fetch_usdt_market_cap_percentage
from eth_signal_bot.notifiers.telegram import build_usdt_dominance_alert_message


@dataclass
class UsdtDominanceMonitor:
    """Track range-entry alerts for CoinGecko USDT market-cap percentage."""

    fetcher: object = fetch_usdt_market_cap_percentage
    sender: object = None
    min_value: float = config.USDT_DOMINANCE_MIN
    max_value: float = config.USDT_DOMINANCE_MAX
    source_url: str = config.COINGECKO_GLOBAL_URL
    last_in_range: bool = False

    def check(self, checked_at=None):
        """Fetch, evaluate, and optionally notify when USDT enters the target range."""
        checked_at = checked_at or datetime.now()

        try:
            value = float(self.fetcher(self.source_url))
        except Exception as exc:
            print(f"   [USDT] CoinGecko check failed: {exc}")
            return {
                "ok": False,
                "value": None,
                "in_range": self.last_in_range,
                "sent": False,
                "error": str(exc),
            }

        in_range = self.min_value <= value <= self.max_value
        should_send = in_range and not self.last_in_range
        self.last_in_range = in_range

        sent = False
        if should_send and self.sender:
            message = build_usdt_dominance_alert_message(
                value,
                self.min_value,
                self.max_value,
                source_url=self.source_url,
                checked_at=checked_at,
            )
            sent = bool(self.sender(message, retries=3))

        status = "trong vùng" if in_range else "ngoài vùng"
        print(f"   [USDT] market_cap_percentage.usdt={value:.4f}% ({status})")
        if should_send:
            print("   [USDT] Da kich hoat canh bao Telegram." if sent else "   [USDT] Gui canh bao that bai.")

        return {
            "ok": True,
            "value": value,
            "in_range": in_range,
            "sent": sent,
            "error": None,
        }
