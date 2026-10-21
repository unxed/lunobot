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


class LocalPathTest(unittest.TestCase):
    def test_tmp_clone_path_is_reported(self):
        line = ("21-10-2026 01:07 UTC (Лунобот-1): шаг 2 припаркован — клон "
                "`/tmp/lunobot-1/work/dn87-2-1020-2245/dn`, sha `a83aaf7`")
        self.assertEqual(gate.local_paths(line), ["/tmp/lunobot-1/work/dn87-2-1020-2245/dn"])

    def test_branch_record_passes(self):
        line = ("21-10-2026 01:07 UTC (Лунобот-1): шаг 2 припаркован — unxed/dn, ветка "
                "`tmp/19d3/dn87-2-1020-2245`, sha `a83aaf76307f666e5da388a587174509145a3695`")
        self.assertEqual(gate.local_paths(line), [])

    def test_other_tmp_paths_are_not_state(self):
        self.assertEqual(gate.local_paths("тест пишет в /tmp/f4-test, а не в рабочий каталог"), [])


if __name__ == "__main__":
    unittest.main()
