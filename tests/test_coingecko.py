import unittest

from eth_signal_bot.exchanges.coingecko import (
    CoinGeckoGlobalError,
    parse_usdt_market_cap_percentage,
)


class CoinGeckoGlobalTests(unittest.TestCase):
    def test_parse_usdt_market_cap_percentage(self):
        payload = {"data": {"market_cap_percentage": {"usdt": 8.45}}}

        self.assertEqual(parse_usdt_market_cap_percentage(payload), 8.45)

    def test_parse_accepts_numeric_string(self):
        payload = {"data": {"market_cap_percentage": {"usdt": "8.41"}}}

        self.assertEqual(parse_usdt_market_cap_percentage(payload), 8.41)

    def test_missing_usdt_field_raises_clear_error(self):
        payload = {"data": {"market_cap_percentage": {}}}

        with self.assertRaises(CoinGeckoGlobalError):
            parse_usdt_market_cap_percentage(payload)

    def test_non_numeric_usdt_field_raises_clear_error(self):
        payload = {"data": {"market_cap_percentage": {"usdt": "not-a-number"}}}

        with self.assertRaises(CoinGeckoGlobalError):
            parse_usdt_market_cap_percentage(payload)


if __name__ == "__main__":
    unittest.main()
