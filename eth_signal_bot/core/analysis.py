"""Market analysis helpers shared by scheduler and dashboard."""
from datetime import datetime
import math

from eth_signal_bot.core import config
from eth_signal_bot.exchanges.binance import fetch_klines, fetch_current_price
from eth_signal_bot.indicators.signals import score_signals
from eth_signal_bot.indicators.zones import calculate_dynamic_zones


def _as_float(value):
    """Convert pandas/numpy scalar values into JSON-safe floats."""
    numeric = float(value)
    if not math.isfinite(numeric):
        return 0.0
    return numeric


def _classify_direction(total_score):
    if total_score >= config.BUY_THRESHOLD:
        return "BUY"
    if total_score <= -config.SELL_THRESHOLD:
        return "SELL"
    return "NEUTRAL"


def _confidence_label(total_score):
    threshold = config.BUY_THRESHOLD if total_score >= 0 else config.SELL_THRESHOLD
    threshold = max(float(threshold), 1.0)
    strength = abs(total_score) / threshold
    if strength >= 1:
        return "Mạnh"
    if strength >= 0.66:
        return "Vừa"
    return "Yếu"


def _direction_label(direction):
    return {
        "BUY": "Thiên MUA",
        "SELL": "Thiên BÁN",
        "NEUTRAL": "Trung lập",
    }[direction]


def _build_summary(direction, confidence, scores):
    if not scores:
        return "Chưa có đủ dữ liệu để tổng hợp tín hiệu."

    sorted_scores = sorted(scores, key=lambda s: abs(s["total_score"]), reverse=True)
    lead = sorted_scores[0]
    lead_signal = lead["signals"][0] if lead["signals"] else "tín hiệu kỹ thuật chưa rõ ràng"
    aligned = sum(
        1
        for score in scores
        if (direction == "BUY" and score["total_score"] > 0)
        or (direction == "SELL" and score["total_score"] < 0)
        or (direction == "NEUTRAL" and score["total_score"] == 0)
    )

    if direction == "BUY":
        return (
            f"Tín hiệu nghiêng về mua ở mức {confidence.lower()}, "
            f"dẫn dắt bởi khung {lead['timeframe']}: {lead_signal}. "
            f"{aligned}/{len(scores)} khung thời gian đang ủng hộ phe mua."
        )
    if direction == "SELL":
        return (
            f"Tín hiệu nghiêng về bán ở mức {confidence.lower()}, "
            f"dẫn dắt bởi khung {lead['timeframe']}: {lead_signal}. "
            f"{aligned}/{len(scores)} khung thời gian đang ủng hộ phe bán."
        )
    return (
        f"Thị trường đang trung lập; khung {lead['timeframe']} có biến động rõ nhất: "
        f"{lead_signal}. Nên chờ thêm xác nhận trước khi vào lệnh."
    )


def _select_primary_zones(zones_by_timeframe):
    """Prefer 4h zones as the main trading map, then fall back to any available frame."""
    if "4h" in zones_by_timeframe:
        return zones_by_timeframe["4h"]
    if "H4" in zones_by_timeframe:
        return zones_by_timeframe["H4"]
    return next(iter(zones_by_timeframe.values()), {})


def analyze_market():
    """Fetch market data and return a normalized analysis snapshot."""
    price_data = fetch_current_price(config.SYMBOL)
    if not price_data:
        return None

    current_price = price_data["price"]
    scores = []
    zones_by_timeframe = {}
    for label, tf_config in config.TIMEFRAMES.items():
        df = fetch_klines(config.SYMBOL, tf_config["interval"], tf_config["limit"])
        if df is not None and len(df) > 50:
            zones = calculate_dynamic_zones(df, current_price)
            zones_by_timeframe[label] = zones
            result = score_signals(df, current_price, label, zones=zones)
            scores.append(
                {
                    "timeframe": result["timeframe"],
                    "total_score": _as_float(result["total_score"]),
                    "buy_score": _as_float(result["buy_score"]),
                    "sell_score": _as_float(result["sell_score"]),
                    "rsi": _as_float(result["rsi"]),
                    "macd_hist": _as_float(result["macd_hist"]),
                    "ema20": _as_float(result["ema20"]),
                    "ema50": _as_float(result["ema50"]),
                    "zones": result["zones"],
                    "signals": list(result["signals"]),
                }
            )

    if not scores:
        return None

    total_score = sum(s["total_score"] for s in scores) / len(scores)
    direction = _classify_direction(total_score)
    confidence = _confidence_label(total_score)
    primary_zones = _select_primary_zones(zones_by_timeframe)

    return {
        "symbol": config.SYMBOL,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "price": _as_float(price_data["price"]),
        "change_24h": _as_float(price_data["change_24h"]),
        "high_24h": _as_float(price_data["high_24h"]),
        "low_24h": _as_float(price_data["low_24h"]),
        "volume": _as_float(price_data["volume"]),
        "total_score": _as_float(total_score),
        "direction": direction,
        "direction_label": _direction_label(direction),
        "confidence_label": confidence,
        "summary": _build_summary(direction, confidence, scores),
        "timeframes": scores,
        "zones_timeframe": "4h" if "4h" in zones_by_timeframe else next(iter(zones_by_timeframe), None),
        "zones_by_timeframe": zones_by_timeframe,
        "support_zones": list(primary_zones.get("support", [])),
        "resistance_zones": list(primary_zones.get("resistance", [])),
        "fibonacci": dict(primary_zones.get("fib", {})),
        "poc": primary_zones.get("poc"),
        "volume_walls": list(primary_zones.get("volume_walls", [])),
        "swing_high": primary_zones.get("swing_high"),
        "swing_low": primary_zones.get("swing_low"),
        "buy_threshold": config.BUY_THRESHOLD,
        "sell_threshold": config.SELL_THRESHOLD,
        "check_interval": config.CHECK_INTERVAL,
    }
