import json
import unittest
from types import SimpleNamespace
from unittest.mock import call, patch

import sweep


class GhAllTest(unittest.TestCase):
    def test_falls_back_to_explicit_pages_when_paginate_is_blocked(self):
        first = [{"id": n} for n in range(100)]
        second = [{"id": 100}]
        responses = [
            SimpleNamespace(returncode=1, stdout="", stderr="numeric path blocked"),
            SimpleNamespace(returncode=0, stdout=json.dumps(first), stderr=""),
            SimpleNamespace(returncode=0, stdout=json.dumps(second), stderr=""),
        ]
        with patch.object(sweep.subprocess, "run", side_effect=responses) as run:
            result = sweep.gh_all("repos/example/project/branches?per_page=100")

        self.assertEqual(result, first + second)
        self.assertEqual(run.call_args_list, [
            call(["gh", "api", "--paginate", "repos/example/project/branches?per_page=100"],
                 capture_output=True, text=True, timeout=60),
            call(["gh", "api", "repos/example/project/branches?per_page=100&page=1"],
                 capture_output=True, text=True, timeout=30),
            call(["gh", "api", "repos/example/project/branches?per_page=100&page=2"],
                 capture_output=True, text=True, timeout=30),
        ])

    def test_empty_successful_list_is_empty_not_an_access_error(self):
        with patch.object(sweep.subprocess, "run", return_value=SimpleNamespace(
                returncode=0, stdout="[]", stderr="")):
            self.assertEqual(sweep.gh_all("repos/example/project/branches?per_page=100"), [])

    def test_failed_explicit_page_is_not_reported_as_empty(self):
        responses = [
            SimpleNamespace(returncode=1, stdout="", stderr="paginate blocked"),
            SimpleNamespace(returncode=1, stdout="", stderr="access denied"),
        ]
        with patch.object(sweep.subprocess, "run", side_effect=responses):
            self.assertIsNone(sweep.gh_all("repos/example/project/branches?per_page=100"))


if __name__ == "__main__":
    unittest.main()
