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

    def test_empty_paginated_page_falls_back_to_explicit_pages(self):
        expected = [{"number": n} for n in range(1, 159)]
        paginated = done("[[" + ",".join('{"number":%d}' % n for n in range(1, 101)) + "],[]]")
        page_one = done("[" + ",".join('{"number":%d}' % n for n in range(1, 101)) + "]")
        page_two = done("[" + ",".join('{"number":%d}' % n for n in range(101, 159)) + "]")
        with mock.patch("check_triage.shutil.which", return_value="/usr/bin/gh"), \
                mock.patch("check_triage.run_gh", side_effect=[paginated, page_one, page_two]) as run:
            self.assertEqual(
                check_triage.gh_pages("/repos/o/r/issues?per_page=100", expected_count=158),
                expected,
            )
        self.assertEqual(run.call_count, 3)
        self.assertIn("page=1", run.call_args_list[1].args[0][2])
        self.assertIn("page=2", run.call_args_list[2].args[0][2])

    def test_explicit_pagination_does_not_treat_short_page_as_end(self):
        first = done('[{"number":1}]')
        second = done('[{"number":2}]')
        with mock.patch("check_triage.shutil.which", return_value=None), \
                mock.patch("check_triage.urllib.request.urlopen", side_effect=[
                    mock.mock_open(read_data=first.stdout).return_value,
                    mock.mock_open(read_data=second.stdout).return_value,
                ]) as request:
            self.assertEqual(
                check_triage.gh_pages("/repos/o/r/issues", expected_count=2),
                [{"number": 1}, {"number": 2}],
            )
        self.assertEqual(request.call_count, 2)

    def test_incomplete_explicit_pagination_fails_closed(self):
        first = done('[{"number":1}]')
        empty = done("[]")
        with mock.patch("check_triage.shutil.which", return_value="/usr/bin/gh"), \
                mock.patch("check_triage.run_gh", side_effect=[done("[[]]"), first, empty]):
            with self.assertRaisesRegex(RuntimeError, "пагинация неполна"):
                check_triage.gh_pages("/repos/o/r/issues", expected_count=2)


if __name__ == "__main__":
    unittest.main()
