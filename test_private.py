"""Учётная копия может иметь произвольное имя и быть закрытой."""

import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import check_dispatch
import fleet_watch
import janitor
import sweep


class PrivateAccountingTest(unittest.TestCase):
    def test_sweep_uses_accounting_origin(self):
        remote = SimpleNamespace(stdout="git@github.com:example/private-accounting.git\n")
        with patch.object(sweep.subprocess, "run", return_value=remote):
            repos = sweep.repos()
        self.assertEqual(repos[0], "example/private-accounting")

    def test_dispatch_accepts_private_accounting_clone(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "projects" / "sample"
            project.mkdir(parents=True)
            (root / "LUNOBOT.md").touch()
            (root / "projects" / "INDEX.md").touch()
            path = project / "DISPATCH.md"
            path.touch()
            with patch.object(check_dispatch.subprocess, "run",
                              return_value=SimpleNamespace(stdout=str(root) + os.linesep)):
                self.assertIsNone(check_dispatch.wrong_place(str(path)))

    def test_pr_route_is_valid_for_simple_project(self):
        self.assertIsNone(check_dispatch.route_error(
            "Я Лунобот-2, взял задачу https://github.com/example/project/issues/1 [pr]"))
        self.assertIsNotNone(check_dispatch.route_error(
            "Я Лунобот-2, взял задачу https://github.com/example/project/issues/1 [pr: later]"))

    def test_owner_queue_is_visible_to_watch(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "OWNER_QUEUE.md").write_text(
                "## f4-1628\nАдресат: Лунобот-1\nСостояние: свободно\n",
                encoding="utf-8")
            with patch.object(fleet_watch, "ROOT", directory), \
                 patch.object(fleet_watch, "projects", return_value=[]):
                self.assertEqual(fleet_watch.free_work(),
                                 ["очередь f4-1628 (Лунобот-1)"])

    def test_janitor_uses_trailer_not_deleted_actor(self):
        log = ("@@LUNOBOT-COMMIT@@100\tЛунобот-1 (node a721a6d1487257292ae00780; LNX)\n"
               "-Лунобот-2 (node 91d86915909d88ed7991a74c; LNX)\n")
        with patch.object(janitor.subprocess, "run",
                          return_value=SimpleNamespace(stdout=log)):
            self.assertEqual(janitor.last_seen(),
                             {("1", "a721a6d1487257292ae00780"): 100})

    def test_janitor_does_not_treat_inaccessible_private_repo_as_empty(self):
        with patch.object(janitor.shutil, "which", return_value=None), \
             patch.object(janitor, "gh", return_value=None):
            self.assertIsNone(janitor.gh_all("/repos/example/private/branches?per_page=100"))


if __name__ == "__main__":
    unittest.main()
