"""Проверки гейта check_status_times.py: метки позже текущего UTC."""

import unittest
from datetime import datetime, timezone

import check_status_times as gate

NOW = datetime(2026, 10, 17, 14, 30, 0, tzinfo=timezone.utc)


class FutureStampTest(unittest.TestCase):
    def test_past_and_equal_stamps_pass(self):
        self.assertEqual(gate.future_stamps("17-10-2026 14:20 UTC (Лунобот-1): шаг", NOW), [])
        self.assertEqual(gate.future_stamps("17-10-2026 14:30:00 UTC", NOW), [])

    def test_slack_of_a_minute_is_allowed(self):
        self.assertEqual(gate.future_stamps("17-10-2026 14:30:59 UTC", NOW), [])

    def test_future_stamp_is_reported(self):
        self.assertEqual(gate.future_stamps("17-10-2026 14:40 UTC (Лунобот-1): шаг", NOW), ["17-10-2026 14:40 UTC"])
        self.assertEqual(gate.future_stamps("18-10-2026 00:00:01 UTC", NOW), ["18-10-2026 00:00:01 UTC"])

    def test_dates_without_utc_time_are_not_stamps(self):
        self.assertEqual(gate.future_stamps("релиз 20-10-2026, до 25-10-2026 15:00 по плану", NOW), [])

    def test_impossible_date_is_ignored(self):
        self.assertEqual(gate.future_stamps("31-02-2027 10:00 UTC", NOW), [])


if __name__ == "__main__":
    unittest.main()
