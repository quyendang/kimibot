"""CoinGecko API client helpers."""


class CoinGeckoGlobalError(Exception):
    """Raised when CoinGecko global data cannot be fetched or parsed."""


def parse_usdt_market_cap_percentage(payload):
    """Extract USDT market-cap percentage from CoinGecko global payload."""
    try:
        value = payload["data"]["market_cap_percentage"]["usdt"]
        return float(value)
    except (KeyError, TypeError, ValueError) as exc:
        raise CoinGeckoGlobalError("Missing or invalid data.market_cap_percentage.usdt") from exc


def fetch_usdt_market_cap_percentage(url, timeout=10):
    """Fetch USDT market-cap percentage from CoinGecko global API."""
    try:
        import requests

        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return parse_usdt_market_cap_percentage(response.json())
    except CoinGeckoGlobalError:
        raise
    except Exception as exc:
        raise CoinGeckoGlobalError(f"CoinGecko global fetch failed: {exc}") from exc
