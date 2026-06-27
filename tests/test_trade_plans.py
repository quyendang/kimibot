import unittest

from eth_signal_bot.core import config
from eth_signal_bot.core.trade_plan import build_trade_plans


class TradePlanTests(unittest.TestCase):
    def setUp(self):
        self.original_buy_threshold = config.BUY_THRESHOLD
        self.original_sell_threshold = config.SELL_THRESHOLD
        config.BUY_THRESHOLD = 3
        config.SELL_THRESHOLD = 3

    def tearDown(self):
        config.BUY_THRESHOLD = self.original_buy_threshold
        config.SELL_THRESHOLD = self.original_sell_threshold

    def test_buy_plan_uses_nearest_support_and_is_ready_near_entry(self):
        zones = {
            "support": [1900, 1988],
            "resistance": [2060],
            "poc": 1970,
        }

        plans, active = build_trade_plans(2000, 3, "BUY", zones)
        buy = next(plan for plan in plans if plan["side"] == "BUY")

        self.assertEqual(active["side"], "BUY")
        self.assertEqual(buy["status"], "ready")
        self.assertEqual(buy["reference_label"], "Hỗ trợ")
        self.assertEqual(buy["reference_price"], 1988)
        self.assertLess(buy["stop_loss"], buy["entry_low"])
        self.assertEqual(buy["targets"], [2060])

    def test_sell_plan_uses_nearest_resistance_and_is_ready_near_entry(self):
        zones = {
            "support": [1940],
            "resistance": [2010, 2080],
            "poc": 2030,
        }

        plans, active = build_trade_plans(2000, -3, "SELL", zones)
        sell = next(plan for plan in plans if plan["side"] == "SELL")

        self.assertEqual(active["side"], "SELL")
        self.assertEqual(sell["status"], "ready")
        self.assertEqual(sell["reference_label"], "Kháng cự")
        self.assertEqual(sell["reference_price"], 2010)
        self.assertGreater(sell["stop_loss"], sell["entry_high"])
        self.assertEqual(sell["targets"], [1940])

    def test_favored_plan_waits_when_price_is_far_from_entry(self):
        zones = {
            "support": [1988],
            "resistance": [2200],
        }

        plans, active = build_trade_plans(2100, 3, "BUY", zones)
        buy = next(plan for plan in plans if plan["side"] == "BUY")

        self.assertEqual(active["side"], "BUY")
        self.assertEqual(buy["status"], "wait")
        self.assertEqual(buy["status_label"], "Chờ giá về vùng")

    def test_missing_zones_return_unavailable_plans(self):
        plans, active = build_trade_plans(2000, 0, "NEUTRAL", {})

        self.assertIsNone(active)
        self.assertEqual([plan["status"] for plan in plans], ["unavailable", "unavailable"])


if __name__ == "__main__":
    unittest.main()
