import tempfile
import unittest
from pathlib import Path
from unittest import mock

import janitor

BAD = "??????? ???? ?????? ? ???????? ????? ??????? ??????."


def fake_gh_all(comments, issues):
    def f(path):
        if "/issues/comments" in path:
            return comments
        if "/issues?" in path:
            return issues
        raise AssertionError(path)
    return f


class MojibakeBodies(unittest.TestCase):
    def run_janitor(self, comments, issues):
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(janitor, "gh_all", fake_gh_all(comments, issues)), \
                mock.patch.object(janitor, "trusted_author", lambda: getattr(self, "author", None)):
            janitor.mojibake(Path(d), "o/r")
            f = Path(d) / "MOJIBAKE.md"
            return f.read_text(encoding="utf-8") if f.exists() else None

    def test_pr_and_issue_bodies_reported(self):
        issues = [
            {"number": 15, "html_url": "https://github.com/o/r/pull/15", "body": BAD,
             "user": {"login": "u", "type": "User"}, "updated_at": "t", "pull_request": {}},
            {"number": 7, "html_url": "https://github.com/o/r/issues/7", "body": BAD,
             "user": {"login": "u", "type": "User"}, "updated_at": "t"},
            {"number": 8, "html_url": "https://github.com/o/r/issues/8", "body": BAD,
             "user": {"login": "b", "type": "Bot"}, "updated_at": "t"},
            {"number": 9, "html_url": "https://github.com/o/r/issues/9",
             "body": "Нормальный русский текст тикета.",
             "user": {"login": "u", "type": "User"}, "updated_at": "t"},
        ]
        text = self.run_janitor([], issues)
        self.assertIsNotNone(text)
        self.assertIn("https://github.com/o/r/pull/15 (#15, тело тикета/PR", text)
        self.assertIn("gh_post.py pr-body o/r 15", text)
        self.assertIn("https://github.com/o/r/issues/7 (#7, тело тикета/PR", text)
        self.assertIn("gh_post.py issue-body o/r 7", text)
        self.assertNotIn("gh api -X PATCH", text)
        self.assertNotIn("/issues/8", text)
        self.assertNotIn("/issues/9", text)

    def test_only_trusted_author_texts_reported(self):
        issues = [
            {"number": 1, "html_url": "https://github.com/o/r/issues/1", "body": BAD,
             "user": {"login": "owner", "type": "User"}, "updated_at": "t"},
            {"number": 2, "html_url": "https://github.com/o/r/issues/2", "body": BAD,
             "user": {"login": "reporter", "type": "User"}, "updated_at": "t"},
        ]
        comments = [
            {"id": 5, "html_url": "https://github.com/o/r/issues/2#c5", "body": BAD,
             "user": {"login": "reporter", "type": "User"}, "created_at": "t"},
            {"id": 6, "html_url": "https://github.com/o/r/issues/2#c6", "body": BAD,
             "user": {"login": "owner", "type": "User"}, "created_at": "t"},
        ]
        self.author = "owner"
        text = self.run_janitor(comments, issues)
        self.assertIn("/issues/1", text)
        self.assertIn("#c6", text)
        self.assertNotIn("/issues/2 ", text)
        self.assertNotIn("#c5", text)

    def test_trusted_author_read_from_owner_queue(self):
        self.assertTrue(janitor.trusted_author())

    def test_clean_bodies_no_file(self):
        issues = [{"number": 1, "html_url": "u", "body": "Всё хорошо.",
                   "user": {"login": "u", "type": "User"}, "updated_at": "t"}]
        self.assertIsNone(self.run_janitor([], issues))

    def test_no_access_to_issues_keeps_comment_scan(self):
        self.assertIsNone(self.run_janitor([], None))


if __name__ == "__main__":
    unittest.main()
