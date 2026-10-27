import os
import subprocess
import tempfile
import unittest
from pathlib import Path


RUNNER = Path(__file__).resolve().parents[1] / "runners" / "lunobot-round-luna-high.sh"


class RunnerDeadlineTests(unittest.TestCase):
    def test_prompt_deadline_includes_early_persistence_cutoff(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env = os.environ.copy()
            env["HOME"] = temp_dir
            result = subprocess.run(
                [
                    "bash",
                    "-c",
                    'source "$1"; runner_deadline_instructions "$2"',
                    "test-runner-deadline",
                    str(RUNNER),
                    "0",
                ],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )

        self.assertEqual(
            result.stdout,
            "The runner will forcibly stop this round at about "
            "1970-01-01 00:29:50 UTC; treat 1970-01-01 00:25:50 UTC as the "
            "persistence deadline. Pass both deadlines to every worker, do not "
            "start a step that cannot be safely parked, and push completed "
            "work by the persistence deadline.",
        )


if __name__ == "__main__":
    unittest.main()
