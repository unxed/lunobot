import datetime as dt
import unittest
from unittest import mock

import close_candidates as cc

NOW = dt.datetime(2026, 10, 16, tzinfo=dt.timezone.utc)


def comment(login, day, kind="User"):
    return {"user": {"login": login, "type": kind}, "created_at": f"2026-10-{day:02d}T10:00:00Z"}


class CandidatesTest(unittest.TestCase):
    def run_one(self, labels, comments):
        issue = {"labels": [{"name": n} for n in labels]}
        rows = [{"number": "7", "state": "проверяют"}]
        with mock.patch.object(cc, "api_issue", return_value=issue), \
                mock.patch.object(cc, "api", return_value=comments):
            return cc.candidates(rows, "unxed/f4", 14, now=NOW)

    def test_enhancement_is_never_a_candidate(self):
        out, skipped = self.run_one(["enhancement"], [])
        self.assertEqual(out, [])
        self.assertIn("нет метки bug", skipped[0][1])

    def test_bug_without_recent_human_comment(self):
        out, _ = self.run_one(["bug"], [comment("someone", 1), comment("unxed", 15), comment("bot", 15, "Bot")])
        self.assertEqual([n for n, _, _ in out], [7])

    def test_recent_human_comment_blocks(self):
        out, skipped = self.run_one(["bug"], [comment("someone", 10)])
        self.assertEqual(out, [])
        self.assertIn("моложе", skipped[0][1])

    def test_unlabelled_is_skipped(self):
        out, skipped = self.run_one([], [])
        self.assertEqual(out, [])
        self.assertIn("без меток", skipped[0][1])


if __name__ == "__main__":
    unittest.main()
