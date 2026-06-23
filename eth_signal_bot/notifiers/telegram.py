"""Telegram notification helpers."""
from datetime import datetime
import html
import time
import requests

from eth_signal_bot.core import config


def escape_html(text):
    """Escape characters for Telegram HTML parse mode."""
    return html.escape(str(text))


def send_telegram(message, retries=1):
    """Send an HTML message via Telegram Bot API with optional retries."""
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        print("[WARN] Chua cau hinh Telegram Bot Token / Chat ID!")
        return False

    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": config.TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}

    for attempt in range(1, retries + 1):
        try:
            response = requests.post(url, json=payload, timeout=15)
            if response.status_code == 200:
                return True
            print(f"[ERROR] Telegram HTTP {response.status_code}: {response.text[:300]}")
        except Exception as e:
            print(f"[ERROR] Send Telegram failed (attempt {attempt}/{retries}): {e}")
        if attempt < retries:
            time.sleep(2)

    return False


def _format_scores(scores, total_score):
    """Shared score formatting for alert and summary."""
    lines = []
    for s in scores:
        tf = s["timeframe"]
        score = s["total_score"]
        icon = "🟢" if score > 0 else "🔴" if score < 0 else "⚪"
        lines.append(
            f"   {icon} <b>{tf}</b>: {score:+.0f} diem\n"
            f"      RSI: {s['rsi']:.1f} | MACD Hist: {s['macd_hist']:+.2f}\n"
            f"      EMA20: ${s['ema20']:,.0f} | EMA50: ${s['ema50']:,.0f}"
        )
    return "\n".join(lines)


def build_alert_message(price_data, scores, total_score):
    """Build the alert message payload."""
    now = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    price = price_data["price"]
    change = price_data["change_24h"]

    if total_score >= config.BUY_THRESHOLD:
        action = "🟢 BUY SIGNAL"
        emoji = "🚀"
    elif total_score <= -config.SELL_THRESHOLD:
        action = "🔴 SELL SIGNAL"
        emoji = "📉"
    else:
        action = "⚪ TRUNG TINH"
        emoji = "➖"

    symbol = escape_html(config.SYMBOL)

    msg = f"""{emoji} <b>{symbol} - {action}</b>
⏰ <i>{now}</i>

💰 Gia: <b>${price:,.2f}</b> ({change:+.2f}%)
📊 Diem tong hop: <b>{total_score:+.1f}</b> (3 khung)

📈 Chi tiet chi bao:
{_format_scores(scores, total_score)}

🎯 Vung giao dich:
   🟢 Mua: ${config.SUPPORT_ZONES[0]} / ${config.SUPPORT_ZONES[1]} / ${config.SUPPORT_ZONES[2]}
   🔴 Ban:  ${config.RESISTANCE_ZONES[0]} / ${config.RESISTANCE_ZONES[1]} / ${config.RESISTANCE_ZONES[2]}"""

    return msg


def build_summary_message(price_data, scores, total_score):
    """Build a periodic summary report."""
    now = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    price = price_data["price"]
    change = price_data["change_24h"]

    if total_score >= config.BUY_THRESHOLD:
        bias = "🟢 Thien ve MUA"
    elif total_score <= -config.SELL_THRESHOLD:
        bias = "🔴 Thien ve BAN"
    else:
        bias = "⚪ TRUNG TINH"

    symbol = escape_html(config.SYMBOL)

    msg = f"""📋 <b>{symbol} - Bao cao tong ket 12h</b>
⏰ <i>{now}</i>

💰 Gia: <b>${price:,.2f}</b> ({change:+.2f}%)
📊 Diem tong hop: <b>{total_score:+.1f}</b> — {bias}

📈 Chi tiet chi bao:
{_format_scores(scores, total_score)}

🎯 Vung giao dich:
   🟢 Mua: ${config.SUPPORT_ZONES[0]} / ${config.SUPPORT_ZONES[1]} / ${config.SUPPORT_ZONES[2]}
   🔴 Ban:  ${config.RESISTANCE_ZONES[0]} / ${config.RESISTANCE_ZONES[1]} / ${config.RESISTANCE_ZONES[2]}"""

    return msg


def build_startup_message():
    """Build a startup heartbeat message."""
    now = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    symbol = escape_html(config.SYMBOL)
    timeframes = escape_html(", ".join(config.TIMEFRAMES.keys()))

    # Dung HTML entity thay vi dau < de tranh loi parse tag
    sell_threshold_text = f"&lt;= {-config.SELL_THRESHOLD}"

    return f"""🤖 <b>{symbol} Signal Bot da khoi chay</b>
⏰ <i>{now}</i>

✅ Bot dang chay va san sang gui tin hieu.
⏱ Tan suat quet: {config.CHECK_INTERVAL}s ({config.CHECK_INTERVAL // 60} phut)
🎯 Buy threshold: >= {config.BUY_THRESHOLD}
🎯 Sell threshold: {sell_threshold_text}

📊 Khung thoi gian: {timeframes}"""


def send_startup_notification():
    """Send startup heartbeat to Telegram with retries."""
    message = build_startup_message()
    success = send_telegram(message, retries=3)
    if success:
        print("   ✅ Da gui tin nhan khoi chay Telegram!")
    else:
        print("   ❌ Gui tin nhan khoi chay Telegram that bai sau 3 lan thu!")
    return success
