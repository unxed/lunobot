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


if __name__ == "__main__":
    unittest.main()
