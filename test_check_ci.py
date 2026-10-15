"""Проверки гейта check_ci.py: пустая ссылка на прогон или PR."""

import os
import tempfile
import unittest

import check_ci

HEAD = "# CI \u2014 dn\n\n"
OK = ("15-10-2026 09:56:36 \u041b\u0443\u043d\u043e\u0431\u043e\u0442-1 (node 19d368003c6c048e43dbec70; LNX), "
      "PR [#83](https://github.com/unxed/dn/pull/83), \u043f\u0440\u043e\u0433\u043e\u043d "
      "[#709](https://github.com/unxed/dn/actions/runs/38716477731)")


def kinds(text):
    with tempfile.TemporaryDirectory() as d:
        os.mkdir(os.path.join(d, "projects"))
        os.mkdir(os.path.join(d, "projects", "dn"))
        path = os.path.join(d, "projects", "dn", "CI.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(HEAD + text + "\n")
        return [p[0] for p in check_ci.check(path)[1]]


class EmptyLinkTest(unittest.TestCase):
    def test_full_line_is_fine(self):
        self.assertEqual(kinds(OK), [])

    def test_empty_run_number_is_a_problem(self):
        bad = OK.replace("[#709](https://github.com/unxed/dn/actions/runs/38716477731)",
                         "[#](https://github.com/unxed/dn/actions/runs/)")
        self.assertEqual(kinds(bad), ["\u043f\u0443\u0441\u0442\u0430\u044f \u0441\u0441\u044b\u043b\u043a\u0430"])

    def test_empty_pull_number_is_a_problem(self):
        bad = OK.replace("[#83](https://github.com/unxed/dn/pull/83)", "[#](https://github.com/unxed/dn/pull/)")
        self.assertEqual(len(kinds(bad)), 1)


if __name__ == "__main__":
    unittest.main()
