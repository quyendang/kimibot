"""Signal scoring logic."""
from eth_signal_bot.core import config
from eth_signal_bot.indicators.technicals import calculate_rsi, calculate_ema, calculate_macd


def score_signals(df, current_price, label):
    """
    Score Buy/Sell signals across -5 to +5.
    Positive = Buy, Negative = Sell.
    """
    close = df["close"]

    buy_score = 0
    sell_score = 0
    signals = []

    # 1. RSI
    rsi = calculate_rsi(close, 14).iloc[-1]
    if rsi < 30:
        buy_score += 2
        signals.append(f"RSI {rsi:.1f} < 30 (Qua ban)")
    elif rsi < 40:
        buy_score += 1
        signals.append(f"RSI {rsi:.1f} < 40 (Gan ban)")
    elif rsi > 70:
        sell_score += 2
        signals.append(f"RSI {rsi:.1f} > 70 (Qua mua)")
    elif rsi > 60:
        sell_score += 1
        signals.append(f"RSI {rsi:.1f} > 60 (Gan mua)")

    # 2. MACD
    macd_line, signal_line, histogram = calculate_macd(close)
    hist_val = histogram.iloc[-1]
    hist_prev = histogram.iloc[-2] if len(histogram) > 1 else 0

    if hist_val > 0 and hist_prev <= 0:
        buy_score += 2
        signals.append("MACD Crossover (Mua)")
    elif hist_val > 0:
        buy_score += 1
        signals.append(f"MACD histogram duong ({hist_val:.2f})")
    elif hist_val < 0 and hist_prev >= 0:
        sell_score += 2
        signals.append("MACD Crossunder (Ban)")
    elif hist_val < 0:
        sell_score += 1
        signals.append(f"MACD histogram am ({hist_val:.2f})")

    # 3. EMA Trend
    ema20 = calculate_ema(close, 20).iloc[-1]
    ema50 = calculate_ema(close, 50).iloc[-1]

    if current_price > ema20 > ema50:
        buy_score += 1
        signals.append("Gia > EMA20 > EMA50 (Bullish)")
    elif current_price < ema20 < ema50:
        sell_score += 1
        signals.append("Gia < EMA20 < EMA50 (Bearish)")

    # 4. Support / Resistance zones
    for sup in config.SUPPORT_ZONES:
        if abs(current_price - sup) / current_price < 0.01:
            buy_score += 1
            signals.append(f"Gan ho tro ${sup} (Mua)")
            break

    for res in config.RESISTANCE_ZONES:
        if abs(current_price - res) / current_price < 0.01:
            sell_score += 1
            signals.append(f"Gan khang cu ${res} (Ban)")
            break

    # 5. Price position within recent range
    high_20 = close.tail(20).max()
    low_20 = close.tail(20).min()
    range_20 = high_20 - low_20

    if range_20 > 0:
        position = (current_price - low_20) / range_20
        if position < 0.2:
            buy_score += 1
            signals.append(f"Gia o day 20 nen ({position:.0%})")
        elif position > 0.8:
            sell_score += 1
            signals.append(f"Gia o dinh 20 nen ({position:.0%})")

    total_score = buy_score - sell_score
    return {
        "timeframe": label,
        "total_score": total_score,
        "buy_score": buy_score,
        "sell_score": sell_score,
        "rsi": rsi,
        "macd_hist": hist_val,
        "ema20": ema20,
        "ema50": ema50,
        "signals": signals,
    }
