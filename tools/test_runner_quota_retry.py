import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


RUNNER = Path(__file__).resolve().parents[1] / "runners" / "lunobot-round-luna-high.sh"
CLAUDE_RUNNER = Path(__file__).resolve().parents[1] / "runners" / "lunobot-round-claude.sh"


class RunnerQuotaRetryTests(unittest.TestCase):
    def call_runner_function(self, function, log_path):
        with tempfile.TemporaryDirectory() as home:
            env = os.environ.copy()
            env["HOME"] = home
            result = subprocess.run(
                ["bash", "-c", 'source "$1"; shift; "$@"', "bash", str(RUNNER), function, str(log_path)],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
            return result.stdout.strip()

    def call_claude_function(self, function, *args):
        with tempfile.TemporaryDirectory() as home:
            env = os.environ.copy()
            env["HOME"] = home
            result = subprocess.run(
                ["bash", "-c", 'source "$1" sonnet; shift; "$@"', "bash", str(CLAUDE_RUNNER), function, *map(str, args)],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
            return result.stdout.strip()

    def test_parses_dated_claude_weekly_reset_from_final_result(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "quota.log"
            log.write_text(
                json.dumps({"type": "result", "result": "You've hit your weekly limit · resets Nov 10, 7pm (UTC)"}) + "\n",
                encoding="utf-8",
            )
            self.assertEqual(
                self.call_claude_function("quota_wait_seconds", log, "2026-11-06T09:00:00Z"),
                "381605",
            )

    def test_uses_claude_fallback_without_explicit_reset(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "quota.log"
            log.write_text(
                json.dumps({"type": "result", "result": "You've hit your weekly limit"}) + "\n",
                encoding="utf-8",
            )
            self.assertEqual(
                self.call_claude_function("quota_wait_seconds", log, "2026-11-06T09:00:00Z"),
                "600",
            )

    def test_detects_opencode_provider_quota_and_uses_provider_reset(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "quota.log"
            body = json.dumps({"error": {"type": "usage_limit_reached", "resets_in_seconds": 12752}})
            event = {
                "type": "error",
                "error": {
                    "type": "provider.quota",
                    "response": {"body": body},
                },
            }
            log.write_text(json.dumps(event) + "\n", encoding="utf-8")

            self.assertEqual(self.call_runner_function("check_token_limit", log), "")
            self.assertEqual(self.call_runner_function("quota_wait_seconds", log), "12757")

    def test_uses_configured_fallback_when_provider_has_no_reset(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "quota.log"
            event = {"type": "error", "error": {"type": "provider.quota"}}
            log.write_text(json.dumps(event) + "\n", encoding="utf-8")

            self.assertEqual(self.call_runner_function("quota_wait_seconds", log), "120")


if __name__ == "__main__":
    unittest.main()
