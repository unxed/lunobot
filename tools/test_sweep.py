import io
import json
import unittest
from contextlib import redirect_stderr
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


class TrainBranchesTest(unittest.TestCase):
    def sweep_train(self, state, age_hours):
        deleted = []
        branch = [{"name": "lunobot/train/f4/261007-2302", "commit": {"sha": "abc"}}]

        def fake_gh(path, *args):
            if args[:1] == ("-X",):
                deleted.append(path)
            return None

        with patch.object(sweep, "gh_all", return_value=branch), \
                patch.object(sweep, "gh", side_effect=fake_gh), \
                patch.object(sweep, "pr_state", return_value=state), \
                patch.object(sweep, "age_of", return_value=sweep.timedelta(hours=age_hours)):
            n = sweep.branches(True, set(), ["unxed/f4"])
        return n, deleted

    def test_merged_train_older_than_a_day_is_deleted(self):
        n, deleted = self.sweep_train("closed", 25)
        self.assertEqual(n, 1)
        self.assertEqual(deleted, ["repos/unxed/f4/git/refs/heads/lunobot/train/f4/261007-2302"])

    def test_train_in_flight_or_being_cut_stays(self):
        for state in ("open", "none"):
            self.assertEqual(self.sweep_train(state, 48), (0, []))

    def test_fresh_merged_train_stays(self):
        self.assertEqual(self.sweep_train("closed", 2), (0, []))


class UnreachableRepoTest(unittest.TestCase):
    def test_unreachable_repo_is_skipped_and_the_next_one_is_swept(self):
        deleted = []
        trains = [{"name": "lunobot/train/f4/261007-2302", "commit": {"sha": "abc"}}]

        def fake_gh_all(path):
            return None if path.startswith("repos/unxed/keytrans/") else trains

        def fake_gh(path, *args):
            if args[:1] == ("-X",):
                deleted.append(path)
            return None

        err = io.StringIO()
        with patch.object(sweep, "gh_all", side_effect=fake_gh_all), \
                patch.object(sweep, "gh", side_effect=fake_gh), \
                patch.object(sweep, "pr_state", return_value="closed"), \
                patch.object(sweep, "age_of", return_value=sweep.timedelta(hours=25)), \
                redirect_stderr(err):
            n = sweep.branches(True, set(), ["unxed/keytrans", "unxed/f4"])
            sweep.stale_prs(set(), ["unxed/keytrans"])
        self.assertEqual(n, 1)
        # Недоступность видна, а не выдаётся за пустой список.
        self.assertIn("branch unxed/keytrans: список веток недоступен", err.getvalue())
        self.assertIn("pr     unxed/keytrans: список PR недоступен", err.getvalue())
        self.assertEqual(deleted, ["repos/unxed/f4/git/refs/heads/lunobot/train/f4/261007-2302"])


class PrStateTest(unittest.TestCase):
    def test_unreadable_pr_list_is_unknown_not_none(self):
        with patch.object(sweep, "gh", return_value=None):
            self.assertEqual(sweep.pr_state("unxed/f4", "tmp/19d3/x"), "unknown")

    def test_temp_branch_with_unreadable_pr_list_is_not_deleted(self):
        deleted = []
        temp = [{"name": "tmp/19d3/probe", "commit": {"sha": "abc"}}]

        def fake_gh(path, *args):
            if args[:1] == ("-X",):
                deleted.append(path)
            return None

        with patch.object(sweep, "gh_all", return_value=temp), \
                patch.object(sweep, "gh", side_effect=fake_gh), \
                patch.object(sweep, "age_of", return_value=sweep.timedelta(hours=48)):
            n = sweep.branches(True, set(), ["unxed/f4"])
        self.assertEqual((n, deleted), (0, []))


class ReferencesTest(unittest.TestCase):
    def test_references_read_closes_files(self):
        import gc
        import os
        import tempfile
        import warnings

        with tempfile.TemporaryDirectory() as tmp:
            project = os.path.join(tmp, "projects", "sample")
            os.makedirs(os.path.join(project, "status"))
            with open(os.path.join(project, "DISPATCH.md"), "w", encoding="utf-8") as f:
                f.write("захват /tmp/clone-1\n")
            with open(os.path.join(project, "status", "1.md"), "w", encoding="utf-8") as f:
                f.write("ветка feature/x\n")
            with patch.object(sweep, "ROOT", tmp), warnings.catch_warnings(record=True) as seen:
                warnings.simplefilter("always", ResourceWarning)
                text = sweep.references()
                gc.collect()
        self.assertFalse([w for w in seen if issubclass(w.category, ResourceWarning)])
        self.assertIn("/tmp/clone-1", text)
        self.assertIn("feature/x", text)


if __name__ == "__main__":
    unittest.main()
