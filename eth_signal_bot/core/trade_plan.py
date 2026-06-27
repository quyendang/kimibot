"""Conservative dashboard trade-plan helpers."""
import math

from eth_signal_bot.core import config


ENTRY_BAND_PCT = 0.004
ENTRY_READY_PCT = 0.006
STOP_BUFFER_PCT = 0.012


def _as_float(value):
    numeric = float(value)
    if not math.isfinite(numeric):
        return 0.0
    return numeric


def _round_price(value):
    if value is None:
        return None
    return round(_as_float(value), 2)


def _level_items(zones):
    """Flatten technical levels into labeled price items."""
    items = []

    for value in zones.get("support", []):
        items.append({"kind": "support", "label": "Hỗ trợ", "price": _round_price(value)})
    for value in zones.get("resistance", []):
        items.append({"kind": "resistance", "label": "Kháng cự", "price": _round_price(value)})
    for ratio, value in zones.get("fib", {}).items():
        items.append({"kind": "fib", "label": f"Fib {ratio}", "price": _round_price(value)})

    poc = zones.get("poc")
    if poc:
        items.append({"kind": "poc", "label": "POC", "price": _round_price(poc)})

    for wall in zones.get("volume_walls", []):
        price = wall.get("price") if isinstance(wall, dict) else wall
        items.append({"kind": "volume_wall", "label": "Volume wall", "price": _round_price(price)})

    deduped = {}
    for item in items:
        price = item.get("price")
        if price and price > 0:
            key = round(price, 1)
            deduped.setdefault(key, item)
    return list(deduped.values())


def _pick_entry_level(levels, current_price, side):
    if current_price <= 0:
        return None

    if side == "BUY":
        preferred_kinds = {"support", "fib", "poc", "volume_wall"}
        candidates = [
            level
            for level in levels
            if level["kind"] in preferred_kinds
            and level["price"] <= current_price * (1 + ENTRY_READY_PCT)
            and abs(level["price"] - current_price) / current_price <= 0.08
        ]
        if not candidates:
            candidates = [
                level
                for level in levels
                if level["kind"] in preferred_kinds
                and level["price"] < current_price
            ]
        return max(candidates, key=lambda level: level["price"]) if candidates else None

    preferred_kinds = {"resistance", "fib", "poc", "volume_wall"}
    candidates = [
        level
        for level in levels
        if level["kind"] in preferred_kinds
        and level["price"] >= current_price * (1 - ENTRY_READY_PCT)
        and abs(level["price"] - current_price) / current_price <= 0.08
    ]
    if not candidates:
        candidates = [
            level
            for level in levels
            if level["kind"] in preferred_kinds
            and level["price"] > current_price
        ]
    return min(candidates, key=lambda level: level["price"]) if candidates else None


def _target_levels(levels, current_price, side, entry_price):
    if side == "BUY":
        candidates = [
            level["price"]
            for level in levels
            if level["price"] > max(current_price, entry_price) * (1 + ENTRY_BAND_PCT)
        ]
        return sorted(set(_round_price(price) for price in candidates))[:3]

    candidates = [
        level["price"]
        for level in levels
        if level["price"] < min(current_price, entry_price) * (1 - ENTRY_BAND_PCT)
    ]
    return sorted(set(_round_price(price) for price in candidates), reverse=True)[:3]


def _build_trade_plan(side, current_price, total_score, direction, zones):
    levels = _level_items(zones)
    threshold = config.BUY_THRESHOLD if side == "BUY" else config.SELL_THRESHOLD
    favored = direction == side
    entry = _pick_entry_level(levels, current_price, side)

    if not entry:
        return {
            "side": side,
            "status": "unavailable",
            "status_label": "Thiếu vùng giá",
            "entry_low": None,
            "entry_high": None,
            "entry_label": "Chưa đủ dữ liệu vùng giá",
            "reference_price": None,
            "reference_label": None,
            "trigger": "Chờ bot có lại vùng hỗ trợ/kháng cự rõ ràng.",
            "stop_loss": None,
            "targets": [],
            "reason": "Không có đủ support/resistance/Fib/POC gần giá hiện tại.",
        }

    entry_price = entry["price"]
    band = max(current_price * ENTRY_BAND_PCT, 1.0)
    ready_distance = abs(current_price - entry_price) / current_price
    has_score = total_score >= threshold if side == "BUY" else total_score <= -threshold
    is_ready = favored and has_score and ready_distance <= ENTRY_READY_PCT

    if side == "BUY":
        entry_low = entry_price - band
        entry_high = entry_price + band
        stop_loss = entry_low - max(entry_price * STOP_BUFFER_PCT, band)
        trigger = (
            f"Chỉ mua khi score >= +{threshold} và giá giữ trên "
            f"{entry['label']} ${entry_price:,.0f}."
        )
    else:
        entry_low = entry_price - band
        entry_high = entry_price + band
        stop_loss = entry_high + max(entry_price * STOP_BUFFER_PCT, band)
        trigger = (
            f"Chỉ bán khi score <= -{threshold} và giá bị từ chối tại "
            f"{entry['label']} ${entry_price:,.0f}."
        )

    if is_ready:
        status = "ready"
        status_label = "Có thể canh vào"
    elif favored:
        status = "wait"
        status_label = "Chờ giá về vùng"
    else:
        status = "not_favored"
        status_label = "Chưa ưu tiên"

    return {
        "side": side,
        "status": status,
        "status_label": status_label,
        "entry_low": _round_price(entry_low),
        "entry_high": _round_price(entry_high),
        "entry_label": f"{_round_price(entry_low):,.2f} - {_round_price(entry_high):,.2f}",
        "reference_price": _round_price(entry_price),
        "reference_label": entry["label"],
        "trigger": trigger,
        "stop_loss": _round_price(stop_loss),
        "targets": _target_levels(levels, current_price, side, entry_price),
        "reason": (
            f"Vùng vào dựa trên {entry['label']} gần nhất; trạng thái phụ thuộc "
            "score tổng hợp và khoảng cách giá hiện tại."
        ),
    }


def build_trade_plans(current_price, total_score, direction, zones):
    """Build conservative trade plans for the dashboard snapshot."""
    if not zones:
        zones = {}

    plans = [
        _build_trade_plan("BUY", current_price, total_score, direction, zones),
        _build_trade_plan("SELL", current_price, total_score, direction, zones),
    ]
    active_plan = next(
        (plan for plan in plans if plan["side"] == direction and plan["status"] != "unavailable"),
        None,
    )
    return plans, active_plan
