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

    def test_trailer_attributes_commit_to_actor_not_deleted_claim(self):
        stamp = int(datetime.now(timezone.utc).timestamp())
        log = (f"@@LUNOBOT-COMMIT@@{stamp}\tf4 #926: исправил проверку\t"
               f"Лунобот-1 (node {NODE_1}; LNX)\n"
               f"-взял Лунобот-2 (node {NODE_2}; LNX)\n")
        with patch.object(status.subprocess, "run", return_value=SimpleNamespace(stdout=log)):
            items = status.instances()
        self.assertEqual(len(items), 1)
        self.assertIn("Лунобот-1", items[0]["who"])
        self.assertEqual(items[0]["last"], "f4 #926: исправил проверку")

    def test_legacy_commit_uses_only_added_lines(self):
        stamp = int(datetime.now(timezone.utc).timestamp())
        log = (f"@@LUNOBOT-COMMIT@@{stamp}\tf4 #926: взял шаг\t\n"
               f"-Лунобот-2 (node {NODE_2}; LNX)\n"
               f"+Лунобот-1 (node {NODE_1}; LNX)\n")
        with patch.object(status.subprocess, "run", return_value=SimpleNamespace(stdout=log)):
            items = status.instances()
        self.assertEqual(len(items), 1)
        self.assertIn("Лунобот-1", items[0]["who"])

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
