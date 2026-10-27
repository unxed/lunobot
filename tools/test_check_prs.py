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


    def test_upstream_owner_is_people_and_gh_login_is_us(self):
        # blue-panels/mcommander#418: the owner's own PR upstream; repo owner blue-panels is not "us"
        commits = [{"author": {"login": "unxed"},
                    "commit": {"author": {"email": "1151423+unxed@users.noreply.github.com"},
                               "committer": {"date": "2026-10-20T21:44:17Z"}}}]
        pr = {"created_at": "2026-10-15T11:35:31Z"}
        evs = check_prs.events(pr, [c("2026-10-15T11:39:21Z", "unxed")], [], [], commits, "unxed")
        self.assertIsNone(check_prs.waiting(evs))
        evs = check_prs.events(pr, [c("2026-10-21T08:00:00Z", "blue-panels")], [], [], commits, "unxed")
        self.assertEqual(check_prs.waiting(evs), "2026-10-21T08:00:00Z")

    def test_bot_identity_commit_is_ours(self):
        # unxed/goWidgets#29: Lunobot-2 commits, the noreply address maps to the unrelated GitHub user "lunobot"
        commits = [{"author": {"login": "lunobot"},
                    "commit": {"author": {"email": "lunobot@users.noreply.github.com"},
                               "committer": {"date": "2026-10-20T03:05:16Z"}}}]
        evs = check_prs.events(PR, [c("2026-10-19T23:11:59Z", "unxed")], [], [], commits, "unxed")
        self.assertIsNone(check_prs.waiting(evs))


class HoldsTest(unittest.TestCase):
    def test_parse_owner_hold_lines(self):
        text = ("# f4\n\n- Код: https://github.com/unxed/f4\n"
                "- PR не трогать: #1818 — https://github.com/unxed/f4/pull/1818#issuecomment-6171866633\n"
                "- PR не трогать: #7\n- PR: ветка\n")
        self.assertEqual(check_prs.holds(text),
                         {1818: "https://github.com/unxed/f4/pull/1818#issuecomment-6171866633", 7: ""})
        self.assertEqual(check_prs.repo_of(text), "unxed/f4")

    def test_no_holds(self):
        self.assertEqual(check_prs.holds("- PR: ветка -> PR -> мерж\n- PR не трогать без слова владельца\n"), {})


class BotBranchTest(unittest.TestCase):
    def test_lunobot_branches_are_excluded(self):
        for ref in ("lunobot/pr/fix", "agent/lunobot1/topic", "agent/lunobot2/zipgui-5b-navigation"):
            with self.subTest(ref=ref):
                self.assertTrue(check_prs.is_bot_branch(ref))

    def test_human_agent_branches_remain_eligible(self):
        for ref in ("agent/alice/topic", "agent/lunobot-tools/topic", "agent/lunobotish/topic"):
            with self.subTest(ref=ref):
                self.assertFalse(check_prs.is_bot_branch(ref))

    def test_real_passports_parse(self):
        import os
        root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "projects")
        for p in sorted(os.listdir(root)):
            path = os.path.join(root, p, "PROJECT.md")
            if os.path.exists(path):
                with open(path, encoding="utf-8") as f:
                    text = f.read()
                check_prs.repo_of(text)
                check_prs.holds(text)


if __name__ == "__main__":
    unittest.main()
