import unittest

import triage_touch

TABLE = (
    "| тикет | приоритет | состояние | комментариев | updatedAt |\n"
    "| --- | --- | --- | --- | --- |\n"
    "| 285 | 5 | в пути | 29 | 2026-10-14T12:21:31Z |\n"
    "| 1729 | 3! | проверяют | 18 | 2026-10-14T23:39:46Z |\n"
)


class TouchRowTest(unittest.TestCase):
    def test_updates_counters_keeps_state_and_priority(self):
        text, changed = triage_touch.touch_row(TABLE, 1729, 19, "2026-10-15T00:31:26Z")
        self.assertTrue(changed)
        self.assertIn("| 1729 | 3! | проверяют | 19 | 2026-10-15T00:31:26Z |", text)
        self.assertIn("| 285 | 5 | в пути | 29 | 2026-10-14T12:21:31Z |", text)

    def test_state_change(self):
        text, _ = triage_touch.touch_row(TABLE, 285, 30, "2026-10-15T01:00:00Z", "проверяют")
        self.assertIn("| 285 | 5 | проверяют | 30 | 2026-10-15T01:00:00Z |", text)

    def test_unchanged_reported(self):
        _, changed = triage_touch.touch_row(TABLE, 285, 29, "2026-10-14T12:21:31Z")
        self.assertFalse(changed)

    def test_missing_ticket(self):
        with self.assertRaises(ValueError):
            triage_touch.touch_row(TABLE, 7, 1, "x")

    def test_new_ticket_with_priority_appended_after_last_row(self):
        text, changed = triage_touch.touch_row(TABLE, 1960, 0, "2026-10-15T09:00:00Z", None, "3")
        self.assertTrue(changed)
        self.assertTrue(text.endswith("| 1729 | 3! | проверяют | 18 | 2026-10-14T23:39:46Z |\n| 1960 | 3 | свободен | 0 | 2026-10-15T09:00:00Z |\n"))
        self.assertEqual(text.count("| 1960 |"), 1)

    def test_new_ticket_in_empty_table_goes_after_header(self):
        empty = "# TRIAGE\n\n" + TABLE.split("| 285")[0]
        text, changed = triage_touch.touch_row(empty, 80, 0, "z", None, "5")
        self.assertTrue(changed)
        self.assertEqual(text, empty + "| 80 | 5 | свободен | 0 | z |\n")
        with self.assertRaises(ValueError):
            triage_touch.touch_row(empty, 80, 0, "z")

    def test_new_ticket_with_state(self):
        text, _ = triage_touch.touch_row(TABLE, 1960, 2, "z", "ждёт ответа", "4")
        self.assertIn("| 1960 | 4 | ждёт ответа | 2 | z |", text)

    def test_existing_ticket_ignores_priority(self):
        text, _ = triage_touch.touch_row(TABLE, 1729, 19, "z", None, "1")
        self.assertIn("| 1729 | 3! | проверяют | 19 | z |", text)

    def test_header_preserved(self):
        text, _ = triage_touch.touch_row(TABLE, 285, 30, "z")
        self.assertTrue(text.startswith("| тикет |"))


class ArgumentsTest(unittest.TestCase):
    def test_state_without_value(self):
        with self.assertRaises(ValueError):
            triage_touch.main(["f4", "285", "--state"])

    def test_unknown_option(self):
        with self.assertRaises(ValueError):
            triage_touch.main(["f4", "285", "--foo"])

    def test_bad_priority(self):
        for bad in (["--priority"], ["--priority", "9"]):
            with self.assertRaises(ValueError):
                triage_touch.main(["f4", "285"] + bad)

    def test_bad_state(self):
        with self.assertRaises(ValueError):
            triage_touch.main(["f4", "285", "--state", "foo"])


if __name__ == "__main__":
    unittest.main()
