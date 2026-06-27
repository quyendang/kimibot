"""Main scheduling / analysis loop."""
from datetime import datetime, timedelta
import time

from eth_signal_bot.core import config
from eth_signal_bot.core.analysis import analyze_market
from eth_signal_bot.core.usdt_dominance import UsdtDominanceMonitor
from eth_signal_bot.notifiers.telegram import (
    send_telegram,
    build_alert_message,
    build_summary_message,
)


def analyze_and_alert(force_summary=False):
    """Analyze market and send Telegram alert if threshold met."""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Dang phan tich {config.SYMBOL}...")

    snapshot = analyze_market()
    if not snapshot:
        return None

    price_data = {
        "price": snapshot["price"],
        "change_24h": snapshot["change_24h"],
        "high_24h": snapshot["high_24h"],
        "low_24h": snapshot["low_24h"],
        "volume": snapshot["volume"],
    }
    scores = snapshot["timeframes"]
    total_score = snapshot["total_score"]
    market_zones = {
        "timeframe": snapshot.get("zones_timeframe"),
        "support_zones": snapshot.get("support_zones", []),
        "resistance_zones": snapshot.get("resistance_zones", []),
        "fibonacci": snapshot.get("fibonacci", {}),
        "poc": snapshot.get("poc"),
    }

    print(f"   Gia hien tai: ${price_data['price']:,.2f}")
    for result in scores:
        print(
            f"   {result['timeframe']}: Score={result['total_score']:+.0f} | "
            f"RSI={result['rsi']:.1f} | MACD={result['macd_hist']:+.2f}"
        )
    print(f"   Tong diem: {total_score:+.1f}")

    should_alert = total_score >= config.BUY_THRESHOLD or total_score <= -config.SELL_THRESHOLD

    if should_alert:
        message = build_alert_message(price_data, scores, total_score, market_zones=market_zones)
        success = send_telegram(message, retries=3)
        if success:
            print("   ✅ Da gui thong bao Telegram!")
        else:
            print("   ❌ Gui Telegram that bai!")
            print(f"\n{'='*60}")
            print(message)
            print(f"{'='*60}")
    elif force_summary:
        message = build_summary_message(price_data, scores, total_score, market_zones=market_zones)
        success = send_telegram(message, retries=3)
        if success:
            print("   ✅ Da gui bao cao tong ket Telegram!")
        else:
            print("   ❌ Gui bao cao tong ket that bai!")
    else:
        print(f"   ⚪ Chua du dieu kien ({total_score:+.1f}), cho them...")

    return price_data, scores, total_score


def main_loop():
    """Run the bot continuously."""
    print("=" * 60)
    print("  ETH/USDT Signal Bot - Telegram Alerts")
    print(f"  Check interval: {config.CHECK_INTERVAL}s ({config.CHECK_INTERVAL // 60} phut)")
    print(f"  Buy threshold:  >= {config.BUY_THRESHOLD}")
    print(f"  Sell threshold: <= {-config.SELL_THRESHOLD}")
    print(
        "  USDT dominance: "
        f"{config.USDT_DOMINANCE_MIN:.2f}% - {config.USDT_DOMINANCE_MAX:.2f}% "
        f"every {config.USDT_DOMINANCE_CHECK_INTERVAL}s"
    )
    print("=" * 60)

    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        print("\n⚠️  CANH BAO: Chua cau hinh TELEGRAM_BOT_TOKEN hoac TELEGRAM_CHAT_ID!")
        print("   Dat cac bien moi truong trong Railway Variables.")

    usdt_monitor = UsdtDominanceMonitor(sender=send_telegram)

    summary_interval = 12 * 60 * 60  # 12 tieng
    next_summary_at = datetime.now() + timedelta(seconds=summary_interval)
    next_analysis_at = datetime.now()
    next_usdt_check_at = datetime.now()

    while True:
        now = datetime.now()
        if now >= next_analysis_at:
            force_summary = now >= next_summary_at
            analyze_and_alert(force_summary=force_summary)
            next_analysis_at = now + timedelta(seconds=config.CHECK_INTERVAL)

            if force_summary:
                next_summary_at = now + timedelta(seconds=summary_interval)

        if now >= next_usdt_check_at:
            print(f"\n[{now.strftime('%H:%M:%S')}] Kiem tra USDT market cap percentage...")
            usdt_monitor.check(checked_at=now)
            next_usdt_check_at = now + timedelta(seconds=config.USDT_DOMINANCE_CHECK_INTERVAL)

        next_run_at = min(next_analysis_at, next_usdt_check_at)
        sleep_seconds = max(1, min(60, (next_run_at - datetime.now()).total_seconds()))
        time.sleep(sleep_seconds)
