import unittest

import check_prs


def c(ts, login):
    return {"created_at": ts, "user": {"login": login}}


PR = {"created_at": "2026-10-19T10:00:00Z"}


class WaitingTest(unittest.TestCase):
    def test_author_reply_after_ours_waits(self):
        evs = check_prs.events(PR, [c("2026-10-20T09:03:20Z", "unxed"), c("2026-10-20T15:43:43Z", "Zeroes1")],
                               [], [], [], "unxed")
        self.assertEqual(check_prs.waiting(evs), "2026-10-20T15:43:43Z")

    def test_our_answer_last_does_not_wait(self):
        evs = check_prs.events(PR, [c("2026-10-20T15:43:43Z", "Zeroes1"), c("2026-10-20T16:00:00Z", "unxed")],
                               [], [], [], "unxed")
        self.assertIsNone(check_prs.waiting(evs))

    def test_service_bots_and_author_push_count(self):
        commits = [{"author": {"login": "Zeroes1"}, "commit": {"committer": {"date": "2026-10-20T17:00:00Z"}}}]
        evs = check_prs.events(PR, [c("2026-10-20T16:00:00Z", "unxed"), c("2026-10-20T18:00:00Z", "codecov[bot]")],
                               [], [], commits, "unxed")
        self.assertEqual(check_prs.waiting(evs), "2026-10-20T17:00:00Z")

    def test_new_pr_without_our_answer_waits(self):
        self.assertEqual(check_prs.waiting(check_prs.events(PR, [], [], [], [], "unxed")), PR["created_at"])


if __name__ == "__main__":
    unittest.main()
