import os
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

import janitor_kick

NOW = datetime(2026, 10, 21, 16, 30, 0, tzinfo=timezone.utc)


def run(status, created):
    return {"status": status, "created_at": created}


class DueTest(unittest.TestCase):
    def test_no_runs_is_due(self):
        self.assertTrue(janitor_kick.due([], NOW))

    def test_old_completed_run_is_due(self):
        self.assertTrue(janitor_kick.due([run("completed", "2026-10-21T13:12:03Z")], NOW))

    def test_fresh_run_is_not_due(self):
        self.assertFalse(janitor_kick.due([run("completed", "2026-10-21T16:25:00Z")], NOW))

    def test_running_or_queued_run_is_not_due(self):
        self.assertFalse(janitor_kick.due([run("in_progress", "2026-10-21T13:00:00Z")], NOW))
        self.assertFalse(janitor_kick.due([run("queued", "2026-10-21T13:00:00Z")], NOW))


class SlugTest(unittest.TestCase):
    def repo(self, url):
        d = tempfile.mkdtemp()
        subprocess.run(["git", "init", "-q", d], check=True)
        if url:
            subprocess.run(["git", "-C", d, "remote", "add", "origin", url], check=True)
        return d

    def test_github_urls(self):
        self.assertEqual(janitor_kick.slug(self.repo("https://github.com/unxed/lunobot")), "unxed/lunobot")
        self.assertEqual(janitor_kick.slug(self.repo("https://github.com/unxed/lunobot.git")), "unxed/lunobot")
        self.assertEqual(janitor_kick.slug(self.repo("git@github.com:me/acc.git")), "me/acc")

    def test_local_origin_is_not_kicked(self):
        d = self.repo("/tmp/some/bare.git")
        self.assertIsNone(janitor_kick.slug(d))
        with mock.patch.object(janitor_kick, "gh") as gh:
            self.assertEqual(janitor_kick.kick(d), "origin — не GitHub")
            gh.assert_not_called()


class KickTest(unittest.TestCase):
    def setUp(self):
        p = mock.patch.object(janitor_kick, "slug", return_value="unxed/lunobot")
        p.start()
        self.addCleanup(p.stop)

    def gh_seq(self, *results):
        calls = []

        def fake(*args):
            calls.append(args)
            code, out = results[len(calls) - 1]
            return subprocess.CompletedProcess(args, code, out, "boom")
        return calls, fake

    def test_kicks_when_due(self):
        calls, fake = self.gh_seq((0, '{"workflow_runs": [{"status": "completed", "created_at": "2026-10-21T13:12:03Z"}]}'),
                                  (0, ""))
        with mock.patch.object(janitor_kick, "gh", fake):
            self.assertEqual(janitor_kick.kick(now=NOW), "пнул")
        self.assertIn("-X", calls[1])
        self.assertTrue(calls[1][3].endswith("/actions/workflows/janitor.yml/dispatches"))

    def test_no_kick_when_fresh(self):
        calls, fake = self.gh_seq((0, '{"workflow_runs": [{"status": "completed", "created_at": "2026-10-21T16:25:00Z"}]}'))
        with mock.patch.object(janitor_kick, "gh", fake):
            self.assertTrue(janitor_kick.kick(now=NOW).startswith("рано"))
        self.assertEqual(len(calls), 1)

    def test_errors_are_quiet(self):
        calls, fake = self.gh_seq((1, ""))
        with mock.patch.object(janitor_kick, "gh", fake):
            self.assertTrue(janitor_kick.kick(now=NOW).startswith("не прочитать"))

    def test_env_switch(self):
        with mock.patch.dict(os.environ, {"LUNOBOT_NO_KICK": "1"}), mock.patch.object(janitor_kick, "gh") as gh:
            self.assertEqual(janitor_kick.kick(now=NOW), "выключено LUNOBOT_NO_KICK")
            gh.assert_not_called()


if __name__ == "__main__":
    unittest.main()
