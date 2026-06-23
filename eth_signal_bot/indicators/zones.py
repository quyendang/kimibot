"""Dynamic support, resistance, Fibonacci, and volume profile zones."""
import numpy as np

from eth_signal_bot.indicators.technicals import calculate_ema, calculate_ma


def _safe_float(value):
    if value is None:
        return None
    return round(float(value), 2)


def find_pivot_points(df, window=3):
    """Find pivot highs and lows from OHLC data."""
    highs = df["high"].to_numpy()
    lows = df["low"].to_numpy()
    pivot_highs = []
    pivot_lows = []

    for idx in range(window, len(df) - window):
        high_slice = highs[idx - window : idx + window + 1]
        low_slice = lows[idx - window : idx + window + 1]
        if highs[idx] == high_slice.max():
            pivot_highs.append(float(highs[idx]))
        if lows[idx] == low_slice.min():
            pivot_lows.append(float(lows[idx]))

    return sorted(pivot_highs), sorted(pivot_lows)


def cluster_levels(levels, current_price, tolerance=0.015, max_distance=0.18):
    """Cluster nearby price levels and keep levels close to current price."""
    if not levels or current_price <= 0:
        return []

    nearby = [
        float(level)
        for level in levels
        if abs(float(level) - current_price) / current_price < max_distance
    ]
    if not nearby:
        return []

    clusters = []
    current_cluster = [nearby[0]]
    for level in sorted(nearby)[1:]:
        if (level - current_cluster[-1]) / current_price < tolerance:
            current_cluster.append(level)
        else:
            clusters.append(round(float(np.mean(current_cluster)), 2))
            current_cluster = [level]

    clusters.append(round(float(np.mean(current_cluster)), 2))
    return sorted(clusters)


def calculate_volume_profile(df, n_bins=30, lookback=100):
    """Calculate volume profile point of control and high-volume walls."""
    recent = df.tail(lookback)
    price_min = float(recent["low"].min())
    price_max = float(recent["high"].max())
    if price_max <= price_min:
        return None, []

    bin_edges = np.linspace(price_min, price_max, n_bins + 1)
    volume_profile = np.zeros(n_bins)

    for _, row in recent.iterrows():
        low_bin = int((row["low"] - price_min) / (price_max - price_min) * n_bins)
        high_bin = int((row["high"] - price_min) / (price_max - price_min) * n_bins)
        low_bin = max(0, min(low_bin, n_bins - 1))
        high_bin = max(0, min(high_bin, n_bins - 1))

        if low_bin == high_bin:
            volume_profile[low_bin] += row["volume"]
        else:
            vol_per_bin = row["volume"] / (high_bin - low_bin + 1)
            for bin_idx in range(low_bin, min(high_bin + 1, n_bins)):
                volume_profile[bin_idx] += vol_per_bin

    poc_idx = int(np.argmax(volume_profile))
    poc = round(float((bin_edges[poc_idx] + bin_edges[poc_idx + 1]) / 2), 2)
    mean_vol = float(np.mean(volume_profile))
    std_vol = float(np.std(volume_profile))
    walls = []

    for idx, volume in enumerate(volume_profile):
        if volume > mean_vol + 1.5 * std_vol:
            zone_price = round(float((bin_edges[idx] + bin_edges[idx + 1]) / 2), 2)
            walls.append({"price": zone_price, "volume": round(float(volume), 2)})

    return poc, sorted(walls, key=lambda wall: wall["volume"], reverse=True)[:5]


def calculate_fibonacci_levels(df, lookback=60):
    """Calculate Fibonacci retracement levels from recent swing high/low."""
    recent_close = df["close"].tail(lookback)
    swing_high = float(recent_close.max())
    swing_low = float(recent_close.min())
    levels = {}

    if swing_high > swing_low:
        price_range = swing_high - swing_low
        for ratio in (0.236, 0.382, 0.5, 0.618, 0.786):
            levels[str(ratio)] = round(float(swing_low + price_range * ratio), 2)

    return levels, round(swing_high, 2), round(swing_low, 2)


def calculate_dynamic_zones(df, current_price):
    """Calculate dynamic trading zones for one timeframe."""
    close = df["close"]
    pivot_highs, pivot_lows = find_pivot_points(df, window=3)
    poc, volume_walls = calculate_volume_profile(df)
    fib_levels, swing_high, swing_low = calculate_fibonacci_levels(df)

    return {
        "resistance": cluster_levels(pivot_highs, current_price),
        "support": cluster_levels(pivot_lows, current_price),
        "ema9": _safe_float(calculate_ema(close, 9).iloc[-1]),
        "ema20": _safe_float(calculate_ema(close, 20).iloc[-1]),
        "ema50": _safe_float(calculate_ema(close, 50).iloc[-1]),
        "ma20": _safe_float(calculate_ma(close, 20).iloc[-1]),
        "ma50": _safe_float(calculate_ma(close, 50).iloc[-1]),
        "fib": fib_levels,
        "poc": poc,
        "volume_walls": volume_walls,
        "swing_high": swing_high,
        "swing_low": swing_low,
    }
