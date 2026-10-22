import json
import subprocess
import unittest
from unittest import mock

import check_triage


def done(stdout="[]"):
    return subprocess.CompletedProcess(["gh"], 0, stdout, "")


class RunGhTest(unittest.TestCase):
    def test_retries_after_timeout(self):
        timeout = subprocess.TimeoutExpired(["gh"], 60)
        with mock.patch("check_triage.subprocess.run", side_effect=[timeout, timeout, done()]) as run:
            self.assertEqual(check_triage.run_gh(["gh", "api", "x"]).stdout, "[]")
        self.assertEqual(run.call_count, 3)

    def test_gives_up_after_last_attempt(self):
        timeout = subprocess.TimeoutExpired(["gh"], 60)
        with mock.patch("check_triage.subprocess.run", side_effect=timeout) as run:
            with self.assertRaises(subprocess.TimeoutExpired):
                check_triage.run_gh(["gh", "api", "x"])
        self.assertEqual(run.call_count, check_triage.GH_ATTEMPTS)

    def test_other_errors_are_not_retried(self):
        with mock.patch("check_triage.subprocess.run", side_effect=OSError("нет gh")) as run:
            with self.assertRaises(OSError):
                check_triage.run_gh(["gh", "api", "x"])
        self.assertEqual(run.call_count, 1)

    def test_retries_after_transient_network_error(self):
        tls = subprocess.CompletedProcess(["gh"], 1, "", "Get \"https://api.github.com/x\": net/http: TLS handshake timeout")
        with mock.patch("check_triage.subprocess.run", side_effect=[tls, tls, done()]) as run:
            self.assertEqual(check_triage.run_gh(["gh", "api", "x"]).returncode, 0)
        self.assertEqual(run.call_count, 3)

    def test_returns_transient_error_after_last_attempt(self):
        tls = subprocess.CompletedProcess(["gh"], 1, "", "net/http: TLS handshake timeout")
        with mock.patch("check_triage.subprocess.run", return_value=tls) as run:
            self.assertEqual(check_triage.run_gh(["gh", "api", "x"]).returncode, 1)
        self.assertEqual(run.call_count, check_triage.GH_ATTEMPTS)

    def test_other_failures_are_not_retried(self):
        denied = subprocess.CompletedProcess(["gh"], 1, "", "HTTP 404: Not Found")
        with mock.patch("check_triage.subprocess.run", return_value=denied) as run:
            self.assertEqual(check_triage.run_gh(["gh", "api", "x"]).returncode, 1)
        self.assertEqual(run.call_count, 1)

    def test_gh_pages_uses_the_retry(self):
        timeout = subprocess.TimeoutExpired(["gh"], 60)
        with mock.patch("check_triage.shutil.which", return_value="/usr/bin/gh"), \
                mock.patch("check_triage.subprocess.run", side_effect=[timeout, done("[[{\"n\": 1}]]")]):
            self.assertEqual(check_triage.gh_pages("/repos/o/r/issues"), [{"n": 1}])

    def test_gh_pages_falls_back_after_empty_paginate_page_and_walks_numeric_pages(self):
        path = "/repos/o/r/issues?state=open&per_page=100"
        page1 = [{"number": n} for n in range(1, 99)]
        page2 = [{"number": n} for n in range(99, 159)]
        paginated = done(json.dumps([page1, []]))
        with mock.patch("check_triage.shutil.which", return_value="/usr/bin/gh"), \
                mock.patch("check_triage.subprocess.run", side_effect=[
                    paginated,
                    done(json.dumps(page1)),
                    done(json.dumps(page2)),
                    done("[]"),
                ]) as run:
            items = check_triage.gh_pages(path)

        self.assertEqual(len(items), 158)
        self.assertEqual(items[0]["number"], 1)
        self.assertEqual(items[-1]["number"], 158)
        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual(commands[0], ["gh", "api", path, "--paginate", "--slurp"])
        self.assertEqual(commands[1:], [
            ["gh", "api", "/repos/o/r/issues?state=open&per_page=100&page=1"],
            ["gh", "api", "/repos/o/r/issues?state=open&per_page=100&page=2"],
            ["gh", "api", "/repos/o/r/issues?state=open&per_page=100&page=3"],
        ])

    def test_gh_pages_does_not_mask_auth_error_with_numeric_fallback(self):
        denied = subprocess.CompletedProcess(["gh"], 1, "", "HTTP 401: Bad credentials")
        with mock.patch("check_triage.shutil.which", return_value="/usr/bin/gh"), \
                mock.patch("check_triage.subprocess.run", return_value=denied) as run, \
                mock.patch("check_triage.gh_pages_by_number") as fallback:
            with self.assertRaisesRegex(RuntimeError, "HTTP 401"):
                check_triage.gh_pages("/repos/o/r/issues")

        run.assert_called_once_with(["gh", "api", "/repos/o/r/issues", "--paginate", "--slurp"],
                                    capture_output=True, text=True, timeout=60)
        fallback.assert_not_called()

    def test_open_issues_snapshot_retries_when_both_list_and_search_are_empty(self):
        complete = [
            {"number": 1},
            {"number": 2},
            {"number": 3, "pull_request": {"url": "https://api.github.com/repos/o/r/pulls/3"}},
        ]
        with mock.patch("check_triage.gh_pages", return_value=[]), \
                mock.patch("check_triage.gh_one", side_effect=[
                    {"open_issues_count": 3},
                    {"total_count": 2},
                ]), \
                mock.patch("check_triage.gh_pages_by_number", return_value=complete) as fallback:
            issues = check_triage.open_issues_snapshot("o/r", "/repos/o/r/issues?state=open&per_page=100")

        self.assertEqual(set(issues), {1, 2})
        fallback.assert_called_once_with("/repos/o/r/issues?state=open&per_page=100", expected_count=3)

    def test_open_issues_snapshot_does_not_hide_search_auth_error(self):
        with mock.patch("check_triage.gh_one", side_effect=[
                {"open_issues_count": 0}, RuntimeError("HTTP 401: Bad credentials")]), \
                mock.patch("check_triage.gh_pages", return_value=[]) as pages:
            with self.assertRaisesRegex(RuntimeError, "HTTP 401"):
                check_triage.open_issues_snapshot("o/r", "/repos/o/r/issues?state=open&per_page=100")
        pages.assert_called_once_with("/repos/o/r/issues?state=open&per_page=100", expected_count=0)


if __name__ == "__main__":
    unittest.main()
