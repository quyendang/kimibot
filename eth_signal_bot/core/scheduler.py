"""Main scheduling / analysis loop."""
from datetime import datetime, timedelta
import time

from eth_signal_bot.core import config
from eth_signal_bot.exchanges.binance import fetch_klines, fetch_current_price
from eth_signal_bot.indicators.signals import score_signals
from eth_signal_bot.notifiers.telegram import (
    send_telegram,
    build_alert_message,
    build_summary_message,
)


def analyze_and_alert(force_summary=False):
    """Analyze market and send Telegram alert if threshold met."""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Dang phan tich {config.SYMBOL}...")

    price_data = fetch_current_price(config.SYMBOL)
    if not price_data:
        return None

    current_price = price_data["price"]
    print(f"   Gia hien tai: ${current_price:,.2f}")

    scores = []
    for label, tf_config in config.TIMEFRAMES.items():
        df = fetch_klines(config.SYMBOL, tf_config["interval"], tf_config["limit"])
        if df is not None and len(df) > 50:
            result = score_signals(df, current_price, label)
            scores.append(result)
            print(
                f"   {label}: Score={result['total_score']:+.0f} | "
                f"RSI={result['rsi']:.1f} | MACD={result['macd_hist']:+.2f}"
            )

    if not scores:
        print("   Khong du du lieu!")
        return None

    total_score = sum(s["total_score"] for s in scores) / len(scores)
    print(f"   Tong diem: {total_score:+.1f}")

    should_alert = total_score >= config.BUY_THRESHOLD or total_score <= -config.SELL_THRESHOLD

    if should_alert:
        message = build_alert_message(price_data, scores, total_score)
        success = send_telegram(message, retries=3)
        if success:
            print("   ✅ Da gui thong bao Telegram!")
        else:
            print("   ❌ Gui Telegram that bai!")
            print(f"\n{'='*60}")
            print(message)
            print(f"{'='*60}")
    elif force_summary:
        message = build_summary_message(price_data, scores, total_score)
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
    print("=" * 60)

    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        print("\n⚠️  CANH BAO: Chua cau hinh TELEGRAM_BOT_TOKEN hoac TELEGRAM_CHAT_ID!")
        print("   Dat cac bien moi truong trong Railway Variables.")

    analyze_and_alert()

    summary_interval = 12 * 60 * 60  # 12 tieng
    next_summary_at = datetime.now() + timedelta(seconds=summary_interval)

    while True:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Cho {config.CHECK_INTERVAL}s...")
        time.sleep(config.CHECK_INTERVAL)

        now = datetime.now()
        force_summary = now >= next_summary_at
        analyze_and_alert(force_summary=force_summary)

        if force_summary:
            next_summary_at = now + timedelta(seconds=summary_interval)
