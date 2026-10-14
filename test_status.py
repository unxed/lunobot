"""Проверки источника строки «последний след» на пульте."""

import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

import status


NODE_1 = "a721a6d1487257292ae00780"
NODE_2 = "91d86915909d88ed7991a74c"


class InstancesTest(unittest.TestCase):
    def test_only_indexed_projects_are_shown(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("own", "old"):
                project = root / "projects" / name
                project.mkdir(parents=True)
                (project / "PROJECT.md").write_text(
                    f"- Код: https://github.com/example/{name}\n", encoding="utf-8")
            (root / "projects" / "INDEX.md").write_text(
                "1. [own](own/PROJECT.md)\n", encoding="utf-8")
            with patch.object(status, "ROOT", root):
                self.assertEqual([name for name, _, _ in status.projects()], ["own"])

    def test_activity_comes_from_work_repos_with_trailer(self):
        stamp = int(datetime.now(timezone.utc).timestamp())
        commits = [(stamp, "f4 #926: исправил проверку\n\nLunobot-Instance: "
                    f"Лунобот-1 (node {NODE_1}; LNX)\n"),
                   (stamp, "коммит человека без трейлера")]
        with patch.object(status, "work_commits", return_value=commits):
            items = status.instances()
        self.assertEqual(len(items), 1)
        self.assertIn("Лунобот-1", items[0]["who"])
        self.assertEqual(items[0]["last"], "f4 #926: исправил проверку")

    def test_accounting_repo_is_not_activity(self):
        with patch.object(status, "projects", return_value=[]):
            self.assertEqual(status.work_commits(), [])
            self.assertEqual(status.instances(), [])

    def test_work_commits_only_queries_staging_for_train_projects(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            projects = root / "projects"
            for name, publication in (("f4", "поезда"), ("dn", "PR"),
                                      ("vtui", "lunobot/staging + train.py land")):
                project = projects / name
                project.mkdir(parents=True)
                mode = (f"- Режим публикации: {publication}\n" if name != "vtui" else
                        f"- PR: {publication}\n")
                (project / "PROJECT.md").write_text(
                    f"- Код: https://github.com/example/{name}\n{mode}", encoding="utf-8")
            (projects / "INDEX.md").write_text(
                "1. [f4](f4/PROJECT.md)\n2. [dn](dn/PROJECT.md)\n"
                "3. [vtui](vtui/PROJECT.md)\n", encoding="utf-8")
            calls = []

            def api(path):
                calls.append(path)
                return []

            with patch.object(status, "ROOT", root), patch.object(status, "gh_json", side_effect=api):
                status.work_commits()

        self.assertEqual(sum("sha=lunobot%2Fstaging" in call for call in calls), 2)
        self.assertEqual(sum("sha=main" in call for call in calls), 3)

    def test_times_are_localized_in_browser(self):
        with patch.object(status, "instances_block", return_value=[]), \
             patch.object(status, "fleet_line", return_value=""):
            page = status.render_html([])
        self.assertIn("getHours()", page)
        self.assertIn("часовом поясе вашего браузера", page)

    def test_description_is_visible_on_dashboard(self):
        item = {"who": "Лунобот-1", "node": NODE_1[:8], "mins": 3,
                "last": "f4 #926: исправил проверку"}
        with patch.object(status, "instances", return_value=[item]), \
             patch.object(status, "pending_nodes", return_value=set()):
            lines = status.instances_block()
        self.assertEqual(lines, ["Лунобот-1 — последний след 3 мин назад: "
                                 "f4 #926: исправил проверку"])
        with patch.object(status, "instances_block", return_value=lines), \
             patch.object(status, "fleet_line", return_value=""):
            page = status.render_html([])
        self.assertIn("последний след 3 мин назад: f4 #926: исправил проверку", page)


class GitHubRestFallbackTest(unittest.TestCase):
    def test_merged_pull_requests_use_rest_pages_and_cutoff(self):
        calls = []

        def api(path):
            calls.append(path)
            if "page=1" in path:
                return [{"number": 12, "merged_at": "2026-10-10T12:00:00Z",
                         "updated_at": "2026-10-10T12:00:00Z"},
                        {"number": 11, "merged_at": "2026-09-30T12:00:00Z",
                         "updated_at": "2026-09-30T12:00:00Z"}]
            return []

        with patch.object(status, "gh_json", side_effect=api):
            prs = status.merged_pull_requests("example/project", "2026-10-01T00:00:00Z")

        self.assertEqual([p["number"] for p in prs], [12])
        self.assertIn("/repos/example/project/pulls?state=closed", calls[0])
        self.assertIn("page=1", calls[0])

    def test_open_issue_count_subtracts_all_open_pulls(self):
        calls = []

        def api(path):
            calls.append(path)
            if path == "/repos/example/project":
                return {"open_issues_count": 8}
            if "page=1" in path:
                return [{"number": 1}, {"number": 2}, {"number": 3}]
            return []

        with patch.object(status, "gh_json", side_effect=api):
            count = status.open_issue_count("example/project")

        self.assertEqual(count, 5)
        self.assertTrue(any("/repos/example/project/pulls?state=open" in c for c in calls))

    def test_report_surfaces_rest_failures_instead_of_empty_data(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "DISPATCH.md").write_text("# DISPATCH\n", encoding="utf-8")
            (root / "CI.md").write_text("# CI\n", encoding="utf-8")
            with patch.object(status, "effective_now", return_value=datetime.now()), \
                 patch.object(status, "instances", return_value=[]), \
                 patch.object(status, "gh_json", return_value=None), \
                 patch.object(status, "gh_pages", return_value=None):
                blocks = status.report("example", "example/project", root, 24)

        titles = {block[0]: block[1] for block in blocks}
        self.assertIn("Не удалось получить список влитых PR из GitHub API.",
                      titles["Сделано за 24 ч — влитые PR"])
        self.assertIn("Открытых тикетов: недоступно", titles)


if __name__ == "__main__":
    unittest.main()
