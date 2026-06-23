#!/usr/bin/env python3
"""Entry point for ETH/USDT Signal Bot."""
import time

from eth_signal_bot.health.server import start_health_server
from eth_signal_bot.notifiers.telegram import send_startup_notification
from eth_signal_bot.core.scheduler import main_loop


if __name__ == "__main__":
    start_health_server()
    # Doi mot chut de health server va network san sang
    time.sleep(2)
    send_startup_notification()
    main_loop()
