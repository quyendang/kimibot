import unittest
from contextlib import redirect_stdout
from datetime import datetime
from io import StringIO

from eth_signal_bot.core.usdt_dominance import UsdtDominanceMonitor
from eth_signal_bot.notifiers.telegram import build_usdt_dominance_alert_message


class UsdtDominanceMonitorTests(unittest.TestCase):
    def check_silently(self, monitor, **kwargs):
        with redirect_stdout(StringIO()):
            return monitor.check(**kwargs)

    def test_sends_when_value_enters_range(self):
        sent_messages = []
        monitor = UsdtDominanceMonitor(
            fetcher=lambda url: 8.45,
            sender=lambda message, retries=1: sent_messages.append((message, retries)) or True,
            min_value=8.4,
            max_value=8.5,
            source_url="https://example.test/global",
        )

        result = self.check_silently(
            monitor,
            checked_at=datetime(2026, 6, 27, 10, 0, 0),
        )

        self.assertTrue(result["ok"])
        self.assertTrue(result["in_range"])
        self.assertTrue(result["sent"])
        self.assertEqual(len(sent_messages), 1)
        self.assertEqual(sent_messages[0][1], 3)

    def test_does_not_send_repeatedly_while_still_in_range(self):
        sent_messages = []
        monitor = UsdtDominanceMonitor(
            fetcher=lambda url: 8.45,
            sender=lambda message, retries=1: sent_messages.append(message) or True,
            min_value=8.4,
            max_value=8.5,
        )

        first = self.check_silently(monitor)
        second = self.check_silently(monitor)

        self.assertTrue(first["sent"])
        self.assertFalse(second["sent"])
        self.assertEqual(len(sent_messages), 1)

    def test_rearms_after_value_leaves_range(self):
        values = iter([8.45, 8.7, 8.44])
        sent_messages = []
        monitor = UsdtDominanceMonitor(
            fetcher=lambda url: next(values),
            sender=lambda message, retries=1: sent_messages.append(message) or True,
            min_value=8.4,
            max_value=8.5,
        )

        first = self.check_silently(monitor)
        outside = self.check_silently(monitor)
        second = self.check_silently(monitor)

        self.assertTrue(first["sent"])
        self.assertFalse(outside["sent"])
        self.assertTrue(second["sent"])
        self.assertEqual(len(sent_messages), 2)

    def test_fetch_error_does_not_send_or_change_state(self):
        sent_messages = []
        monitor = UsdtDominanceMonitor(
            fetcher=lambda url: (_ for _ in ()).throw(RuntimeError("api down")),
            sender=lambda message, retries=1: sent_messages.append(message) or True,
            min_value=8.4,
            max_value=8.5,
            last_in_range=True,
        )

        result = self.check_silently(monitor)

        self.assertFalse(result["ok"])
        self.assertTrue(result["in_range"])
        self.assertFalse(result["sent"])
        self.assertEqual(sent_messages, [])
        self.assertTrue(monitor.last_in_range)

    def test_message_contains_value_range_and_source(self):
        message = build_usdt_dominance_alert_message(
            8.45,
            8.4,
            8.5,
            source_url="https://example.test/global?a=1&b=2",
            checked_at=datetime(2026, 6, 27, 10, 0, 0),
        )

        self.assertIn("8.4500%", message)
        self.assertIn("8.40% - 8.50%", message)
        self.assertIn("10:00:00 27/06/2026", message)
        self.assertIn("https://example.test/global?a=1&amp;b=2", message)


if __name__ == "__main__":
    unittest.main()
