"""Проверки гейта check_dispatch.py: владелец захвата, пересечение ссылок, повтор строки CI.md."""

import os
import tempfile
import unittest
from pathlib import Path

import check_dispatch

NODE = "19d368003c6c048e43dbec70"
URL = "https://github.com/unxed/dn/issues/40"


def line(ts, num, verb="взял", suffix="; LNX", node=NODE, tail=" [pr]"):
    return f"{ts} Я Лунобот-{num} (node {node}{suffix}), {verb} задачу {URL}{tail}"


class SameNodeDuplicateTest(unittest.TestCase):
    def problems(self, *lines):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "DISPATCH.md")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("# DISPATCH\n\n" + "\n\n".join(lines) + "\n")
            return check_dispatch.check(path, 45)[1]

    def test_other_number_same_node_is_duplicate(self):
        found = self.problems(line("14-10-2026 16:12:49", 2), line("14-10-2026 16:16:13", 1))
        self.assertEqual([p[0] for p in found], ["дубль"])

    def test_other_number_over_foreign_keepalive_is_duplicate(self):
        found = self.problems(line("14-10-2026 16:12:49", 2),
                              line("14-10-2026 16:14:00", 2, verb="работаю", tail=""),
                              line("14-10-2026 16:16:13", 1))
        self.assertEqual([p[0] for p in found], ["дубль"])

    def test_rewritten_under_new_number_is_not_duplicate(self):
        found = self.problems(line("14-10-2026 16:16:13", 1), line("14-10-2026 16:17:00", 1, verb="работаю", tail=""))
        self.assertEqual(found, [])

    def test_same_number_keepalive_is_not_duplicate(self):
        found = self.problems(line("14-10-2026 16:12:49", 1),
                              line("14-10-2026 16:16:13", 1, verb="работаю", tail=""))
        self.assertEqual(found, [])

    def test_other_node_is_race_not_duplicate(self):
        found = self.problems(line("14-10-2026 16:12:49", 2, node="801452e4fd3b9a26f8e6f02c"),
                              line("14-10-2026 16:16:13", 1))
        self.assertEqual([p[0] for p in found], ["гонка"])


OTHER = "801452e4fd3b9a26f8e6f02c"
HEAD = "# DISPATCH — dn\n\n"


def kinds(dispatch, ci=""):
    with tempfile.TemporaryDirectory() as directory:
        project = Path(directory, "projects", "dn")
        project.mkdir(parents=True)
        path = project / "DISPATCH.md"
        path.write_text(HEAD + "\n\n".join(dispatch) + "\n", encoding="utf-8")
        if ci:
            (project / "CI.md").write_text("# CI — dn\n\n" + ci + "\n", encoding="utf-8")
        _, problems = check_dispatch.check(str(path), 45)
    return [kind for kind, _, _ in problems]


class OwnerTest(unittest.TestCase):
    def test_two_numbers_on_one_node_are_different_owners(self):
        found = kinds([
            f"14-10-2026 08:37:22 Я Лунобот-2 (node {NODE}; LNX), взял задачу "
            "https://github.com/unxed/dn/issues/33 (часть 3 из 4) [pr]",
            f"14-10-2026 08:37:54 Я Лунобот-1 (node {NODE}; LNX; воркер a75b78fc), взял задачу "
            "https://github.com/unxed/dn/issues/33 (часть 3 из 4) [pr]"])
        self.assertIn("дубль", found)  # на узле main уже ловит это как «дубль»

    def test_same_session_keepalive_is_not_a_race(self):
        found = kinds([
            f"14-10-2026 08:37:22 Я Лунобот-1 (node {NODE}; LNX), взял задачу "
            "https://github.com/unxed/dn/issues/33 [pr]",
            f"14-10-2026 08:40:00 Я Лунобот-1 (node {NODE}; LNX), работаю над задачей "
            "https://github.com/unxed/dn/issues/33"])
        self.assertEqual(found, [])


class OverlapTest(unittest.TestCase):
    def test_custom_task_and_url_for_same_ticket_overlap(self):
        # 14-10-2026: «влить зелёный PR #49, unxed/dn#33 часть 3 из 4» и захват URL того же тикета
        found = kinds([
            f"14-10-2026 08:37:22 Я Лунобот-2 (node {NODE}; LNX), взял кастомную задачу "
            "«влить зелёный PR #49, unxed/dn#33 часть 3 из 4» по § 5 п. 3 "
            "[urgent: по § 5 п. 3 — доводка созревшей строки CI.md]",
            f"14-10-2026 08:37:54 Я Лунобот-1 (node {NODE}; LNX; воркер a75b78fc), взял задачу "
            "https://github.com/unxed/dn/issues/33 (часть 3 из 4) [pr]"])
        self.assertIn("пересечение", found)

    def test_different_explicit_parts_do_not_overlap(self):
        found = kinds([
            f"14-10-2026 08:37:22 Я Лунобот-2 (node {OTHER}; LNX), взял кастомную задачу "
            "«влить PR unxed/dn#49, unxed/dn#33 часть 2 из 4» по § 5 п. 3 "
            "[urgent: по § 5 п. 3 — доводка созревшей строки CI.md]",
            f"14-10-2026 08:37:54 Я Лунобот-1 (node {NODE}; LNX), взял задачу "
            "https://github.com/unxed/dn/issues/33 (часть 3 из 4) [pr]"])
        self.assertNotIn("пересечение", found)

    def test_one_workers_lines_do_not_overlap_with_itself(self):
        found = kinds([
            f"14-10-2026 08:37:22 Я Лунобот-1 (node {NODE}; LNX; воркер aec573a8), взял "
            "кастомную задачу «довести unxed/dn#54» по § 6 [pr]",
            f"14-10-2026 08:37:54 Я Лунобот-1 (node {NODE}; LNX; воркер aec573a8), взял задачу "
            "https://github.com/unxed/dn/issues/52 (unxed/dn#54) [pr]"])
        self.assertNotIn("пересечение", found)


class CiTest(unittest.TestCase):
    CI = (f"14-10-2026 08:11:41 Лунобот-1 (node {NODE}; LNX), тикет "
          "https://github.com/unxed/dn/issues/52, PR [#54](https://github.com/unxed/dn/pull/54), "
          "коммит `abc1234`, прогон [#1](https://github.com/unxed/dn/actions/runs/1)")

    def test_routine_claim_of_ticket_in_ci_is_rejected(self):
        found = kinds([f"14-10-2026 08:14:27 Я Лунобот-1 (node {OTHER}; LNX), взял задачу "
                       "https://github.com/unxed/dn/issues/52 [pr]"], self.CI)
        self.assertIn("уже в CI.md", found)

    def test_urgent_follow_up_of_ci_line_is_allowed(self):
        found = kinds([f"14-10-2026 08:14:27 Я Лунобот-1 (node {OTHER}; LNX), взял задачу "
                       "https://github.com/unxed/dn/issues/52 "
                       "[urgent: по § 5 п. 3 — доводка созревшей строки CI.md]"], self.CI)
        self.assertNotIn("уже в CI.md", found)

    def test_next_part_of_multipart_ticket_is_allowed(self):
        ci = self.CI.replace("issues/52,", "issues/52 (часть 4 из 6),")
        found = kinds([f"14-10-2026 08:14:27 Я Лунобот-1 (node {OTHER}; LNX), взял задачу "
                       "https://github.com/unxed/dn/issues/52 (часть 5 из 6) [pr]"], ci)
        self.assertNotIn("уже в CI.md", found)


if __name__ == "__main__":
    unittest.main()
