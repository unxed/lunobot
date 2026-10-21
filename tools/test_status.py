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

    def test_numbers_come_with_topic(self):
        status.TOPICS.clear()
        with patch.object(status, "gh_json", return_value={"title": "dn#80: hoist DoIt (unxed/dn#80)"}):
            line = status.with_topic("[#80](u)", "unxed/dn", 80)
            claim = status.key_with_topic("https://github.com/unxed/dn/issues/80", "unxed/dn")
        self.assertEqual(line, "[#80](u) «hoist DoIt»")
        self.assertIn("«hoist DoIt»", claim)
        status.TOPICS.clear()
        with patch.object(status, "gh_json", return_value=None):
            self.assertEqual(status.with_topic("[#1](u)", "unxed/dn", 1), "[#1](u)")
        status.TOPICS.clear()

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


class ShortenKeepsLinksFlatTest(unittest.TestCase):
    """Ссылка в записи учёта остаётся одной ссылкой: адрес, что уже стоит в `[подпись](адрес)`,
    и хеш внутри адреса коммита второй раз ссылкой не становятся."""

    REPO = "example/project"
    SHA = "0123456789abcdef0123456789abcdef01234567"

    def shorten(self, text):
        with patch.dict(status.RUN_NUMBERS, {"39601384825": 6144}):
            return status.shorten(text, self.REPO)

    def test_a_linked_run_stays_as_written(self):
        url = f"https://github.com/{self.REPO}/actions/runs/39601384825"
        self.assertEqual(self.shorten(f"прогон [#6144]({url})"), f"прогон [#6144]({url})")

    def test_a_bare_run_url_becomes_one_link(self):
        url = f"https://github.com/{self.REPO}/actions/runs/39601384825"
        self.assertEqual(self.shorten(url), f"[прогон #6144]({url})")

    def test_linked_and_bare_pull_urls_in_one_line(self):
        a = f"https://github.com/{self.REPO}/pull/5"
        b = f"https://github.com/{self.REPO}/pull/6"
        self.assertEqual(self.shorten(f"[PR #5]({a}) и {b}"), f"[PR #5]({a}) и [PR #6]({b})")

    def test_a_commit_url_is_linked_once(self):
        url = f"https://github.com/{self.REPO}/commit/{self.SHA}"
        self.assertEqual(self.shorten(url), f"[`0123456`]({url})")
        self.assertEqual(self.shorten(f"[`abc1234`]({url})"), f"[`abc1234`]({url})")

    def test_a_bare_hash_still_becomes_a_commit_link(self):
        self.assertEqual(self.shorten(f"коммит {self.SHA}"),
                         f"коммит [`0123456`](https://github.com/{self.REPO}/commit/{self.SHA})")

    def test_no_link_inside_a_link_in_a_ci_row(self):
        row = ("21-10-2026 12:52:13 Лунобот-1 (node 19d368003c6c048e43dbec70; LNX), main, "
               "коммит `3d2f691`, прогон "
               f"[#6144](https://github.com/{self.REPO}/actions/runs/39601384825)")
        with patch.dict(status.RUN_NUMBERS, {"39601384825": 6144}):
            line = status.ci_line(row, self.REPO)
        self.assertNotIn("]([", line)


if __name__ == "__main__":
    unittest.main()
