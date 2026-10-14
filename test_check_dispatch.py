import os
import tempfile
import unittest

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

    def test_same_number_keepalive_is_not_duplicate(self):
        found = self.problems(line("14-10-2026 16:12:49", 1),
                              line("14-10-2026 16:16:13", 1, verb="работаю", tail=""))
        self.assertEqual(found, [])

    def test_other_node_is_race_not_duplicate(self):
        found = self.problems(line("14-10-2026 16:12:49", 2, node="801452e4fd3b9a26f8e6f02c"),
                              line("14-10-2026 16:16:13", 1))
        self.assertEqual([p[0] for p in found], ["гонка"])


if __name__ == "__main__":
    unittest.main()
