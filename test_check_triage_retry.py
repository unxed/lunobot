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


if __name__ == "__main__":
    unittest.main()
