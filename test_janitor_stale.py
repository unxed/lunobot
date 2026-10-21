import unittest
from datetime import datetime, timezone

import janitor

NOW = datetime(2026, 10, 16, 17, 0, 0, tzinfo=timezone.utc).timestamp()
WHO = "Я Лунобот-2 (node 19d368003c6c048e43dbec70; LNX)"


def row(ts, text):
    return f"{ts} {WHO}, {text}"


class HardStale(unittest.TestCase):
    def test_old_row_without_keepalive_is_stale(self):
        b = row("16-10-2026 10:10:08", "взял задачу https://github.com/unxed/f4/issues/1752 [land]")
        self.assertEqual(janitor.hard_stale([b], NOW), [b])

    def test_recent_row_is_kept(self):
        b = row("16-10-2026 15:00:00", "взял задачу https://github.com/unxed/f4/issues/1 [land]")
        self.assertEqual(janitor.hard_stale([b], NOW), [])

    def test_keepalive_with_same_key_extends_the_row(self):
        old = row("16-10-2026 10:00:00", "взял задачу https://github.com/unxed/f4/issues/7 [land]")
        alive = row("16-10-2026 16:30:00", "работаю над задачей https://github.com/unxed/f4/issues/7")
        self.assertEqual(janitor.hard_stale([old, alive], NOW), [])

    def test_custom_task_key_is_the_quoted_text(self):
        old = row("16-10-2026 10:00:00", "взял кастомную задачу «покрыть тестами X» по § 5 п. 6 [land]")
        alive = row("16-10-2026 16:50:00", "работаю над кастомной задачей «покрыть тестами X»")
        other = row("16-10-2026 10:00:00", "взял кастомную задачу «другая» по § 5 п. 6 [land]")
        self.assertEqual(janitor.hard_stale([old, alive, other], NOW), [other])

    def test_worker_suffix_row_is_recognised_and_stale(self):
        b = "16-10-2026 10:10:08 Я Лунобот-2 (node 19d368003c6c048e43dbec70; LNX; воркер ebbd0d075ffe), " \
            "взял задачу https://github.com/unxed/f4/issues/1752 [land]"
        self.assertRegex(b, janitor.WHO)
        self.assertEqual(janitor.hard_stale([b], NOW), [b])

    def test_parked_commit_row_goes_stale_like_any_other(self):
        # припаркованное живёт в ветке и status/ (§ 7.5), захват не вечен
        b = row("16-10-2026 04:10:04", "взял задачу https://github.com/unxed/tv3/issues/3 "
                "(припаркованный коммит 53675ad) [pr]")
        self.assertEqual(janitor.hard_stale([b], NOW), [b])

    def test_urgent_row_goes_stale_after_45_minutes(self):
        b = row("16-10-2026 16:10:00", "взял кастомную задачу «красный staging f4» по § 5 п. 2 "
                "[urgent: по § 5 п. 2 — красный staging]")
        self.assertEqual(janitor.hard_stale([b], NOW), [b])

    def test_urgent_row_younger_than_45_minutes_is_kept(self):
        b = row("16-10-2026 16:30:00", "взял кастомную задачу «красный staging f4» по § 5 п. 2 "
                "[urgent: по § 5 п. 2 — красный staging]")
        self.assertEqual(janitor.hard_stale([b], NOW), [])

    def test_urgent_row_is_extended_by_keepalive(self):
        old = row("16-10-2026 15:00:00", "взял кастомную задачу «красный main» по § 5 п. 2 "
                  "[urgent: по § 5 п. 2 — красный main]")
        alive = row("16-10-2026 16:40:00", "работаю над кастомной задачей «красный main»")
        self.assertEqual(janitor.hard_stale([old, alive], NOW), [])

    def test_urgent_limit_is_strict_and_any_row_of_the_key_makes_it_urgent(self):
        mark = "взял кастомную задачу «красный main» по § 5 п. 2 [urgent: по § 5 п. 2 — красный main]"
        exactly = row("16-10-2026 16:15:00", mark)
        self.assertEqual(janitor.hard_stale([exactly], NOW), [])
        old = row("16-10-2026 15:00:00", mark)
        plain = row("16-10-2026 15:20:00", "работаю над кастомной задачей «красный main»")
        self.assertEqual(janitor.hard_stale([old, plain], NOW), [old, plain])

    def test_other_urgent_reason_keeps_the_long_limit(self):
        b = row("16-10-2026 14:30:00", "взял кастомную задачу «довести PR» по § 5 п. 3 "
                "[urgent: по § 5 п. 3 — зрелая строка CI.md]")
        self.assertEqual(janitor.hard_stale([b], NOW), [])

    def test_non_capture_lines_are_ignored(self):
        b = "16-10-2026 10:00:00 Я Лунобот-1, объявляю заморозку land проекта f4"
        self.assertEqual(janitor.hard_stale([b], NOW), [])


if __name__ == "__main__":
    unittest.main()
