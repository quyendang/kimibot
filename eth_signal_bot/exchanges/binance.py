"""Binance API client helpers."""
import requests
import pandas as pd


def fetch_klines(symbol, interval, limit=200):
    """Fetch OHLCV klines from Binance spot API."""
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        df = pd.DataFrame(
            data,
            columns=[
                "open_time", "open", "high", "low", "close", "volume",
                "close_time", "quote_volume", "trades", "taker_buy_base",
                "taker_buy_quote", "ignore",
            ],
        )

        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)

        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
        return df
    except Exception as e:
        print(f"[ERROR] Fetch data failed: {e}")
        return None


def fetch_current_price(symbol):
    """Fetch current 24h ticker stats."""
    url = "https://api.binance.com/api/v3/ticker/24hr"
    try:
        response = requests.get(url, params={"symbol": symbol}, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {
            "price": float(data["lastPrice"]),
            "change_24h": float(data["priceChangePercent"]),
            "high_24h": float(data["highPrice"]),
            "low_24h": float(data["lowPrice"]),
            "volume": float(data["volume"]),
        }
    except Exception as e:
        print(f"[ERROR] Fetch price failed: {e}")
        return None
