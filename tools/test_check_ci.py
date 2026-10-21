"""Проверки гейта check_ci.py: пустая ссылка на прогон или PR."""

import os
import tempfile
import unittest

import check_ci

HEAD = "# CI \u2014 dn\n\n"
OK = ("15-10-2026 09:56:36 \u041b\u0443\u043d\u043e\u0431\u043e\u0442-1 (node 19d368003c6c048e43dbec70; LNX), "
      "PR [#83](https://github.com/unxed/dn/pull/83), \u043a\u043e\u043c\u043c\u0438\u0442 7f58055, \u043f\u0440\u043e\u0433\u043e\u043d "
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

    def test_empty_commit_sha_is_a_problem(self):
        bad = OK.replace("\u043a\u043e\u043c\u043c\u0438\u0442 7f58055,", "\u043a\u043e\u043c\u043c\u0438\u0442 ,")
        self.assertEqual(kinds(bad), ["\u043f\u0443\u0441\u0442\u043e\u0439 \u043a\u043e\u043c\u043c\u0438\u0442"])

    def test_empty_commit_in_backticks_is_a_problem(self):
        bad = OK.replace("\u043a\u043e\u043c\u043c\u0438\u0442 7f58055,", "\u043a\u043e\u043c\u043c\u0438\u0442 ``,")
        self.assertEqual(kinds(bad), ["\u043f\u0443\u0441\u0442\u043e\u0439 \u043a\u043e\u043c\u043c\u0438\u0442"])

    def test_legal_commit_forms_and_missing_field_are_fine(self):
        for ok in (OK.replace("7f58055", "`7f58055`"),
                   OK.replace("\u043a\u043e\u043c\u043c\u0438\u0442 7f58055, ", "")):
            self.assertEqual(kinds(ok), [])


class ShortTimestampTest(unittest.TestCase):
    SHORT = ("18-10-2026 13:21 UTC (\u041b\u0443\u043d\u043e\u0431\u043e\u0442-1, node 801452e4fd3b9a26f8e6f02c; LNX): "
             "PR https://github.com/unxed/dn/pull/140")

    def test_short_timestamp_before_first_valid_row_is_a_problem(self):
        self.assertEqual(kinds(self.SHORT), ["\u043c\u0435\u0442\u043a\u0430 \u0431\u0435\u0437 \u0441\u0435\u043a\u0443\u043d\u0434"])

    def test_short_timestamp_after_valid_row_is_a_problem(self):
        self.assertEqual(kinds(OK + "\n\n" + self.SHORT), ["\u043c\u0435\u0442\u043a\u0430 \u0431\u0435\u0437 \u0441\u0435\u043a\u0443\u043d\u0434"])

    def test_plain_preamble_is_still_fine(self):
        self.assertEqual(kinds("\u041f\u0440\u043e\u0433\u043e\u043d\u044b, \u043a\u043e\u0442\u043e\u0440\u044b\u0435 \u0437\u0430\u043f\u0443\u0449\u0435\u043d\u044b.\n\n" + OK), [])


if __name__ == "__main__":
    unittest.main()
