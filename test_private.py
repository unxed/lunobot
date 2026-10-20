"""Учётная копия может иметь произвольное имя и быть закрытой."""

import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
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

    def test_dispatch_accepts_relative_path_with_relative_git_root(self):
        cwd = Path.cwd()
        with tempfile.TemporaryDirectory(dir=cwd) as directory:
            root = Path(directory)
            project = root / "projects" / "sample"
            project.mkdir(parents=True)
            (root / "LUNOBOT.md").touch()
            (root / "projects" / "INDEX.md").touch()
            (project / "DISPATCH.md").touch()
            relative_root = os.path.relpath(root, cwd)
            relative_path = os.path.join(relative_root, "projects", "sample", "DISPATCH.md")
            with patch.object(check_dispatch.subprocess, "run",
                              return_value=SimpleNamespace(stdout=relative_root + os.linesep)):
                self.assertIsNone(check_dispatch.wrong_place(relative_path))

    def test_pr_route_is_valid_for_simple_project(self):
        self.assertIsNone(check_dispatch.route_error(
            "Я Лунобот-2, взял задачу https://github.com/example/project/issues/1 [pr]"))
        self.assertIsNotNone(check_dispatch.route_error(
            "Я Лунобот-2, взял задачу https://github.com/example/project/issues/1 [pr: later]"))

    def test_owner_queue_is_visible_to_watch(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "OWNER_QUEUE.md").write_text(
                "шапка\n--\n## f4-1628\nСостояние: свободно\n--\nпросто заметка владельца\n",
                encoding="utf-8")
            with patch.object(fleet_watch, "ROOT", directory), \
                 patch.object(fleet_watch, "projects", return_value=[]):
                self.assertEqual(fleet_watch.free_work(),
                                 ["очередь f4-1628", "очередь просто заметка владельца"])

    def test_watch_counts_workers_per_session(self):
        node = "a721a6d1487257292ae00780"
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory, "projects", "sample")
            project.mkdir(parents=True)
            project.joinpath("DISPATCH.md").write_text(
                f"29-09-2026 08:00:00 Я Лунобот-1 (node {node}; LNX), взял задачу "
                "https://github.com/example/project/issues/1 [pr]\n\n"
                f"29-09-2026 08:01:00 Я Лунобот-2 (node {node}; LNX), взял задачу "
                "https://github.com/example/project/issues/2 [pr]\n\n"
                f"29-09-2026 08:02:00 Я Лунобот-1 (node {node}; LNX), взял задачу "
                "https://github.com/example/project/issues/3 [pr]\n",
                encoding="utf-8")
            with patch.object(fleet_watch, "ROOT", directory), \
                 patch.object(fleet_watch, "projects", return_value=["sample"]):
                self.assertEqual(len(fleet_watch.captures(node)), 3)
                self.assertEqual(len(fleet_watch.captures(node, "1")), 2)
                self.assertEqual(len(fleet_watch.captures(node, "2")), 1)

    def test_fleet_watch_reads_close_files(self):
        import gc
        import warnings

        node = "a721a6d1487257292ae00780"
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory, "projects", "sample")
            project.mkdir(parents=True)
            Path(directory, "projects", "INDEX.md").write_text(
                "1. [sample](sample/PROJECT.md)\n", encoding="utf-8")
            project.joinpath("DISPATCH.md").write_text(
                f"29-09-2026 08:00:00 Я Лунобот-1 (node {node}; LNX), взял задачу "
                "https://github.com/example/project/issues/1 [pr]\n", encoding="utf-8")
            project.joinpath("TRIAGE.md").write_text(
                "| 1 | 3 | свободен | 0 | 2026-10-16T01:00:00Z |\n"
                "| 2 | 4 | свободен | 0 | 2026-10-16T01:00:00Z |\n", encoding="utf-8")
            with patch.object(fleet_watch, "ROOT", directory), \
                 patch.object(fleet_watch, "sh", return_value=(0, "")), \
                 warnings.catch_warnings(record=True) as seen:
                warnings.simplefilter("always", ResourceWarning)
                names = fleet_watch.projects()
                taken = fleet_watch.captures(node)
                free = fleet_watch.free_work()
                gc.collect()
        self.assertFalse([w for w in seen if issubclass(w.category, ResourceWarning)])
        self.assertEqual(names, ["sample"])
        self.assertEqual(len(taken), 1)
        self.assertEqual(free, ["sample#2(п4)"])

    QUEUE = (
        "шапка\n--\n"
        "## stale-1\nСостояние: взял в работу — Лунобот-2 (node n; LNX), 15-10-2026 12:00:00 UTC\n"
        "Прогресс 15-10-2026 16:46:34 UTC (Лунобот-2): шаг\n"
        "Доп. проверка 15-10-2026 18:10 UTC: ещё шаг\n"
        "Доп. шаг 15-10-2026 (без времени): запись только с датой\n"
        "--\n"
        "## fresh-2\nПрогресс 20-10-2026 09:30 UTC\n"
        "Состояние: взял в работу — Лунобот-2 (node n; LNX), 15-10-2026 12:00:00 UTC\n"
        "--\n"
        "## tracked-3\nСостояние: взял в работу — Лунобот-1 (node n; LNX), 15-10-2026 12:00:00 UTC\n"
        "--\n"
        "## tracked-3-other\nСостояние: взял в работу — Лунобот-1 (node n; LNX), 15-10-2026 12:00:00 UTC\n"
        "--\n"
        "## waiting-4\nСостояние: ждёт владельца, не брать; 01-10-2026\n"
        "--\n"
        "## free-5\nСостояние: свободно\n"
        "--\n"
        "## notime-6\nСостояние: взял в работу — Лунобот-2\n"
        "--\n"
        "## lastwins-7\nСостояние: взял в работу — Лунобот-2, 01-10-2026 10:00:00 UTC\n"
        "Состояние: ждёт владельца — вопрос; 02-10-2026 10:00:00 UTC\n"
    )
    NOW = datetime(2026, 10, 20, 10, 0, 0, tzinfo=timezone.utc)

    def stale_queue(self, dispatch, queue=QUEUE, now=NOW):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "OWNER_QUEUE.md").write_text(queue, encoding="utf-8")
            project = Path(directory, "projects", "sample")
            project.mkdir(parents=True)
            project.joinpath("DISPATCH.md").write_text(dispatch, encoding="utf-8")
            with patch.object(fleet_watch, "ROOT", directory), \
                 patch.object(fleet_watch, "projects", return_value=["sample"]):
                return fleet_watch.stale_queue(now)

    def test_stale_queue_flags_only_untracked_claims_without_traces(self):
        dispatch = (
            "20-10-2026 09:55:00 Я Лунобот-1 (node n; LNX), взял кастомную задачу "
            "«tracked-3: действие» по § 8 [urgent: по § 4 п. 1 — поручение владельца]\n")
        found = self.stale_queue(dispatch)
        # tracked-3 держит живой захват; tracked-3-other не путается с ним по префиксу id;
        # fresh-2 — след 20-10 09:30 моложе 90 минут; ждёт владельца/свободно/без метки — не трогаем
        self.assertEqual([i for i, _, _ in found], ["stale-1", "tracked-3-other"])
        # дата без времени считается концом суток: последний след stale-1 — 15-10 23:59:59
        self.assertEqual(found[0][1], datetime(2026, 10, 15, 23, 59, 59, tzinfo=timezone.utc))

    def test_stale_queue_threshold_is_ninety_minutes(self):
        queue = ("шапка\n--\n## x-1\nСостояние: взял в работу — Лунобот-2, "
                 "20-10-2026 08:30:00 UTC\n")
        at = lambda minute: self.stale_queue("", queue,
                                             datetime(2026, 10, 20, 10, minute, 0, tzinfo=timezone.utc))
        self.assertEqual(at(0), [])  # ровно 90 минут — ещё живой
        self.assertEqual([i for i, _, _ in at(1)], ["x-1"])

    def test_stale_queue_keepalive_line_with_block_id_counts_as_live(self):
        dispatch = ("20-10-2026 09:59:00 Я Лунобот-2, работаю над кастомной задачей "
                    "«stale-1: действие»\n")
        self.assertNotIn("stale-1", [i for i, _, _ in self.stale_queue(dispatch)])

    def test_stale_queue_claim_must_sit_inside_one_line_of_quotes(self):
        # незакрытая «ёлочка» в одной строке и закрывающая в другой не склеиваются в чужой захват
        dispatch = "20-10-2026 09:00:00 запись «без закрытия stale-1\nещё строка с » другим текстом\n"
        self.assertIn("stale-1", [i for i, _, _ in self.stale_queue(dispatch)])

    def test_check_prints_stale_queue_event_once_per_repeat_window(self):
        with patch.object(fleet_watch, "sh", return_value=(0, "")), \
             patch.object(fleet_watch, "captures", return_value=[("p", None, "x")] * 4), \
             patch.object(fleet_watch, "staged_repos", return_value=[]), \
             patch.object(fleet_watch, "stale_queue", return_value=[
                 ("stale-1", self.NOW - timedelta(hours=5), "взял в работу — Лунобот-2")]):
            last = {}
            with patch("builtins.print") as shown:
                fleet_watch.check("n", 4, last)
                fleet_watch.check("n", 4, last)
        self.assertEqual(shown.call_count, 1)
        text = shown.call_args[0][0]
        self.assertIn("ПРОТУХ:", text)
        self.assertIn("stale-1", text)
        self.assertIn("ПРОТУХ очередь stale-1", last)

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
