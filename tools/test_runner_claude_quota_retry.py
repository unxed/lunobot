import json
import os
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


RUNNER = Path(__file__).resolve().parents[1] / "runners" / "lunobot-round-claude.sh"


class ClaudeRunnerQuotaRetryTests(unittest.TestCase):
    def call_runner_function(self, function, log_path):
        with tempfile.TemporaryDirectory() as home:
            env = os.environ.copy()
            env["HOME"] = home
            result = subprocess.run(
                ["bash", "-c", 'source "$1" sonnet; shift; "$@"', "bash", str(RUNNER), function, str(log_path)],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
            return result.stdout.strip()

    def test_uses_claude_weekly_reset_time(self):
        now = datetime.now(timezone.utc)
        reset = (now + timedelta(days=2)).replace(hour=19, minute=0, second=0, microsecond=0)
        if reset <= now:
            reset += timedelta(days=1)
        message = f"You've hit your weekly limit · resets {reset.strftime('%b %-d, %I%p')} (UTC)"
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "quota.log"
            log.write_text(json.dumps({"type": "result", "result": message, "subtype": "error"}) + "\n", encoding="utf-8")

            wait = int(self.call_runner_function("quota_wait_seconds", log))

        expected = int((reset - now).total_seconds())
        self.assertGreaterEqual(wait, expected + 4)
        self.assertLessEqual(wait, expected + 7)

    def test_uses_configured_fallback_without_reset_time(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "quota.log"
            log.write_text(json.dumps({"type": "result", "result": "rate limit", "subtype": "error"}) + "\n", encoding="utf-8")

            self.assertEqual(self.call_runner_function("quota_wait_seconds", log), "600")


if __name__ == "__main__":
    unittest.main()
