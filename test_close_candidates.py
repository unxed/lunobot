import datetime as dt
import unittest
from unittest import mock

import close_candidates as cc

NOW = dt.datetime(2026, 10, 16, tzinfo=dt.timezone.utc)


def comment(login, day, kind="User", body=""):
    return {"user": {"login": login, "type": kind}, "created_at": f"2026-10-{day:02d}T10:00:00Z", "body": body}


TRY = comment("unxed", 1, body="Исправлено.\n\n— Пробуйте!\n\n*Лунобот-1*")


class CandidatesTest(unittest.TestCase):
    def run_one(self, labels, comments, author="unxed"):
        issue = {"labels": [{"name": n} for n in labels], "user": {"login": author, "type": "User"},
                 "created_at": "2026-09-01T10:00:00Z"}
        rows = [{"number": "7", "state": "проверяют"}]
        with mock.patch.object(cc, "api_issue", return_value=issue), \
                mock.patch.object(cc, "api", return_value=comments):
            return cc.candidates(rows, "unxed/f4", 14, now=NOW)

    def test_enhancement_is_never_a_candidate(self):
        out, skipped = self.run_one(["enhancement"], [])
        self.assertEqual(out, [])
        self.assertIn("нет метки bug", skipped[0][1])

    def test_bug_without_recent_human_comment(self):
        out, _ = self.run_one(["bug"], [TRY, comment("someone", 1), comment("unxed", 15), comment("bot", 15, "Bot")])
        self.assertEqual([o[0] for o in out], [7])

    def test_recent_human_comment_blocks(self):
        out, skipped = self.run_one(["bug"], [TRY, comment("someone", 10)])
        self.assertEqual(out, [])
        self.assertIn("моложе", skipped[0][1])

    def test_ticket_body_of_a_human_is_a_message(self):
        issue_young = {"labels": [{"name": "bug"}], "user": {"login": "someone", "type": "User"},
                       "created_at": "2026-10-10T10:00:00Z"}
        with mock.patch.object(cc, "api_issue", return_value=issue_young), mock.patch.object(cc, "api", return_value=[]):
            out, skipped = cc.candidates([{"number": "7", "state": "проверяют"}], "unxed/f4", 14, now=NOW)
        self.assertEqual(out, [])
        self.assertIn("моложе", skipped[0][1])

    def test_bulk_list_skips_without_per_issue_request(self):
        bug = {"labels": [{"name": "bug"}], "user": {"login": "unxed", "type": "User"},
               "created_at": "2026-09-01T10:00:00Z"}
        rows = [{"number": "7", "state": "проверяют"}, {"number": "8", "state": "проверяют"}]
        with mock.patch.object(cc, "api_issue", side_effect=AssertionError("per-issue request")), \
                mock.patch.object(cc, "api", return_value=[TRY]):
            out, skipped = cc.candidates(rows, "unxed/f4", 14, now=NOW, bug_issues={7: bug})
        self.assertEqual([o[0] for o in out], [7])
        self.assertEqual([s[0] for s in skipped], [8])

    def test_no_try_comment_is_not_a_candidate(self):
        # Заметки владельца «держим открытым для мониторинга» не подтверждают завершение работы.
        out, skipped = self.run_one(["bug"], [comment("unxed", 1, body="Свой тикет держим открытым для мониторинга.")])
        self.assertEqual(out, [])
        self.assertIn("«Пробуйте!»", skipped[0][1])

    def test_fresh_try_blocks_even_if_reporter_is_old(self):
        # f4#1792: «Пробуйте!» вышло только что, а сообщение автора старше 14 суток — автор не успел проверить.
        fresh = comment("unxed", 15, body="Исправлено.\n\n— Пробуйте!")
        out, skipped = self.run_one(["bug"], [fresh], author="someone")
        self.assertEqual(out, [])
        self.assertIn("не успел проверить", skipped[0][1])

    def test_quoted_try_promise_is_not_evidence(self):
        promise = comment("unxed", 1, body="войдёт в main со следующим поездом; «Пробуйте!» будет отдельным")
        out, _ = self.run_one(["bug"], [promise])
        self.assertEqual(out, [])

    def test_summary_instead_of_try_is_evidence(self):
        out, _ = self.run_one(["bug"], [comment("unxed", 1, body="Итог: причина в апстриме, у нас сделано всё.")])
        self.assertEqual([o[0] for o in out], [7])

    def test_unlabelled_is_skipped(self):
        out, skipped = self.run_one([], [])
        self.assertEqual(out, [])
        self.assertIn("без меток", skipped[0][1])


if __name__ == "__main__":
    unittest.main()
