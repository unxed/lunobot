"""Проверки гейта кодировки gh_post.py и шага janitor, который ищет испорченные комментарии."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import gh_post
import janitor

# Настоящие комментарии, дошедшие до f4#1774 и f4#1778 07-10-2026 (начала).
BROKEN = [
    "???????? native Wayland ?????????.\n\n? ???????????? `github.com/unxed/wayland` (????? `vtui v0.1.396`):",
    "CI ?? ??????? `263a1bce22caaeeac5388399e2d21a923cfdd02f` ??????? ?? ??-?? ??????????????",
    "?? ?? ?? ?? ok",
]
GOOD = [
    "Проверено: текущий f4 main уже использует `github.com/unxed/vtui` v0.1.396.",
    "Почему?? Это же работало. А так? Или так?",
    "Регэксп `a???b` и вывод:\n\n```\n???? \\n ????\n```\n\nвсё в коде, это законно.",
    "Is this the right fix? Please check.",
]


class CheckTextTest(unittest.TestCase):
    def test_real_mojibake_is_rejected(self):
        for text in BROKEN:
            with self.subTest(text=text[:30]):
                self.assertTrue(gh_post.check_text(text))

    def test_normal_text_passes(self):
        for text in GOOD:
            with self.subTest(text=text[:30]):
                self.assertEqual(gh_post.check_text(text), "")

    def test_replacement_char_and_literal_newlines_are_rejected(self):
        self.assertIn("U+FFFD", gh_post.check_text("Текст � сломан"))
        self.assertIn("\\n", gh_post.check_text("Первая строка\\nвторая строка"))

    def test_windows_paths_with_backslash_n_are_not_newlines(self):
        for text in (r"Сейчас при копировании в \\?\nul\ выдаёт ошибку.", r"Файл C:\new\a.txt не найден.",
                     r"Скопируйте на \\?\nul\, /dev/null."):
            with self.subTest(text=text[:30]):
                self.assertEqual(gh_post.check_text(text), "")
        self.assertIn("\\n", gh_post.check_text("Готово.\\nДальше."))
        self.assertIn("\\n", gh_post.check_text("Список:\\n- один\\n- два"))
        self.assertIn("\\n", gh_post.check_text("Files:\\n- a.go"))
        self.assertIn("\\n", gh_post.check_text("На диске C:\\new всё ok:\\nдальше"))

    def test_share_of_question_marks(self):
        self.assertTrue(gh_post.check_text("a? b? c? d? e? f?"))

    def test_file_not_in_utf8_is_rejected(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "body.md"
            path.write_bytes("Привет".encode("cp1251"))
            with self.assertRaises(SystemExit):
                gh_post.gate(str(path))
            path.write_text("Привет, всё в порядке.", encoding="utf-8")
            self.assertEqual(gh_post.gate(str(path)), "Привет, всё в порядке.")


class SignatureLanguageTest(unittest.TestCase):
    RU = "Исправление войдёт в main со следующим поездом, «Пробуйте!» будет отдельным комментарием позже."
    EN = "The fix will land in main with the next train; a separate comment will say when it can be tried."

    def test_signature_must_match_text_language(self):
        self.assertEqual(gh_post.check_signature(self.RU + "\n\n*Лунобот-1 (node a; LNX; Claude Sonnet 5)*"), "")
        self.assertEqual(gh_post.check_signature(self.EN + "\n\n*Lunobot-1 (node a; LNX; Claude Sonnet 5)*"), "")
        self.assertIn("латиницей", gh_post.check_signature(self.RU + "\n\n*Lunobot-1 (node a; LNX)*"))
        self.assertIn("кириллицей", gh_post.check_signature(self.EN + "\n\n*Лунобот-2 (node a; LNX)*"))

    def test_text_without_signature_or_with_little_prose_is_not_checked(self):
        self.assertEqual(gh_post.check_signature(self.RU), "")
        self.assertEqual(gh_post.check_signature("Готово.\n\n*Lunobot-1 (node a; LNX)*"), "")

    def test_code_and_links_do_not_decide_the_language(self):
        text = self.EN + " `исправление`\nhttps://example.com/пробуйте\n```\nпример на русском языке в блоке кода\n```\n\n*Lunobot-1 (node a; LNX)*"
        self.assertEqual(gh_post.check_signature(text), "")

    def test_verbatim_quotes_do_not_decide_the_language(self):
        quote = "<details><summary>Full text</summary>\n\n" + "Architectural proposals for the module, quoted verbatim. " * 20 + "\n\n</details>"
        text = self.RU + "\n\n" + quote + "\n\n> " + self.EN + "\n\n*Лунобот-1 (node a; LNX)*"
        self.assertEqual(gh_post.check_signature(text), "")

    def test_gate_rejects_wrong_signature_with_code_2(self):
        with TemporaryDirectory() as d:
            path = Path(d) / "t.md"
            path.write_text(self.RU + "\n\n*Lunobot-1 (node a; LNX)*\n", encoding="utf-8", newline="")
            with self.assertRaises(SystemExit) as err:
                gh_post.gate(str(path))
            self.assertEqual(err.exception.code, 2)


class VerifyTest(unittest.TestCase):
    def test_comment_that_arrived_broken_is_rewritten_then_deleted(self):
        calls = []

        def fake_api(path, *args, check=True):
            calls.append((path, args))
            return {"body": BROKEN[0], "html_url": "u"}

        with patch.object(gh_post, "api", fake_api), patch.object(gh_post, "gh") as gh:
            self.assertEqual(gh_post.verify_comment("o/r", {"id": 7}, "Нормальный текст", "f"), 1)
        self.assertTrue(any("PATCH" in args for _, args in calls))
        gh.assert_called_once_with("api", "-X", "DELETE", "repos/o/r/issues/comments/7", check=False)

    def test_matching_comment_is_kept(self):
        with patch.object(gh_post, "api", return_value={"body": "Текст\r\n", "html_url": "u"}):
            self.assertEqual(gh_post.verify_comment("o/r", {"id": 7}, "Текст\n", "f"), 0)


class IssueBodyTest(unittest.TestCase):
    def test_issue_body_is_sent_to_issues_and_verified(self):
        calls = []

        def fake_api(path, *args, check=True):
            calls.append((path, args))
            return {"body": "Тело тикета\n", "html_url": "u"}

        with TemporaryDirectory() as directory:
            f = Path(directory) / "b.md"
            f.write_text("Тело тикета\n", encoding="utf-8")
            with patch.object(gh_post, "api", fake_api):
                self.assertEqual(gh_post.main(["issue-body", "o/r", "15", str(f)]), 0)
        self.assertEqual(calls[0], ("repos/o/r/issues/15", ("-X", "PATCH", "-F", f"body=@{f}")))
        self.assertEqual(calls[1], ("repos/o/r/issues/15", ()))
        self.assertFalse(any("pulls" in path for path, _ in calls))

    def test_issue_body_that_stays_broken_fails(self):
        calls = []

        def fake_api(path, *args, check=True):
            calls.append((path, args))
            return {"body": BROKEN[0], "html_url": "u"}

        with patch.object(gh_post, "api", fake_api):
            self.assertEqual(gh_post.verify_body("o/r", "issues", 15, "Нормальный текст", "f"), 1)
        self.assertEqual([a for _, a in calls].count(("-X", "PATCH", "-F", "body=@f")), 1)


class CreateIssueTest(unittest.TestCase):
    def test_issue_is_created_from_file_with_title_and_labels_and_verified(self):
        calls = []

        def fake_api(path, *args, check=True):
            calls.append((path, args))
            if args:
                return {"number": 7, "title": "Заголовок", "body": "Тело\n", "html_url": "u",
                        "labels": [{"name": "Enhancement"}]}
            return {"body": "Тело\n", "html_url": "u"}

        with TemporaryDirectory() as directory:
            f = Path(directory) / "i.md"
            f.write_text("Заголовок\nТело\n", encoding="utf-8")
            with patch.object(gh_post, "api", fake_api):
                self.assertEqual(gh_post.main(["issue", "o/r", str(f), "--label", "enhancement"]), 0)
        self.assertEqual(calls[0][0], "repos/o/r/issues")
        self.assertIn("labels[]=enhancement", calls[0][1])
        self.assertEqual(calls[1], ("repos/o/r/issues/7", ()))

    def test_broken_text_creates_nothing(self):
        with TemporaryDirectory() as directory:
            f = Path(directory) / "i.md"
            f.write_text(BROKEN[0] + "\n", encoding="utf-8")
            with patch.object(gh_post, "api") as api:
                with self.assertRaises(SystemExit) as raised:
                    gh_post.main(["issue", "o/r", str(f)])
        self.assertEqual(raised.exception.code, 2)
        api.assert_not_called()

    def test_title_only_issue_is_not_reported_as_body_mismatch(self):
        calls = []

        def fake_api(path, *args, check=True):
            calls.append((path, args))
            return {"number": 7, "title": "Только заголовок", "body": None, "html_url": "u", "labels": []}

        with TemporaryDirectory() as directory:
            f = Path(directory) / "i.md"
            f.write_text("Только заголовок\n", encoding="utf-8")
            with patch.object(gh_post, "api", fake_api):
                self.assertEqual(gh_post.main(["issue", "o/r", str(f)]), 0)
        self.assertEqual(len(calls), 1)

    def test_label_missing_in_response_is_an_error(self):
        def fake_api(path, *args, check=True):
            return {"number": 7, "title": "Заголовок", "body": "Тело\n", "html_url": "u", "labels": []}

        with TemporaryDirectory() as directory:
            f = Path(directory) / "i.md"
            f.write_text("Заголовок\nТело\n", encoding="utf-8")
            with patch.object(gh_post, "api", fake_api):
                self.assertEqual(gh_post.main(["issue", "o/r", str(f), "--label", "bug"]), 1)

    def test_bad_arguments_create_nothing(self):
        for extra in (["--label"], ["--labels", "bug"], ["--label", "bug", "лишнее"], ["--label", "--label"]):
            with self.subTest(extra=extra), TemporaryDirectory() as directory:
                f = Path(directory) / "i.md"
                f.write_text("Заголовок\nТело\n", encoding="utf-8")
                with patch.object(gh_post, "api") as api:
                    self.assertEqual(gh_post.main(["issue", "o/r", str(f), *extra]), 2)
                api.assert_not_called()
        with patch.object(gh_post, "api") as api:
            self.assertEqual(gh_post.main(["issue", "o/r"]), 2)
        api.assert_not_called()


class SameTextTest(unittest.TestCase):
    def test_identical_claude_footer_is_accepted(self):
        footer = "---\n_Generated by [Claude Code](https://claude.ai/code)_"
        self.assertTrue(gh_post.same_text(f"Текст\n\n{footer}", f"Текст\n\n{footer}"))

    def test_proxy_can_replace_footer_with_other_supported_form(self):
        sent = "Текст\n\n---\n_Generated by [Claude Code](https://claude.ai/code)_"
        stored = "Текст\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n[Session](https://claude.ai/code/session-123)"
        self.assertTrue(gh_post.same_text(stored, sent))

    def test_footer_appended_by_proxy_is_accepted(self):
        stored = "Текст\n\n---\n_Generated by [Claude Code](https://claude.ai/code)_"
        self.assertTrue(gh_post.same_text(stored, "Текст\n"))

    def test_duplicate_claude_footers_are_accepted(self):
        footer = "---\n_Generated by [Claude Code](https://claude.ai/code)_"
        self.assertTrue(gh_post.same_text(f"Текст\n\n{footer}\n\n{footer}", "Текст"))

    def test_broken_text_is_not_the_same(self):
        self.assertFalse(gh_post.same_text("?????", "Текст"))
        self.assertFalse(gh_post.same_text("Текст\n\n?????? ????", "Текст"))
        footer = "---\n_Generated by [Claude Code](https://claude.ai/code)_"
        self.assertFalse(gh_post.same_text(f"Текст ?????\n\n{footer}", f"Текст\n\n{footer}"))


class JanitorMojibakeTest(unittest.TestCase):
    def test_file_lists_broken_comments_and_disappears_when_fixed(self):
        comment = {"id": 1, "html_url": "https://x/1", "created_at": "t",
                   "user": {"login": "unxed", "type": "User"}, "body": BROKEN[1]}
        bot = dict(comment, id=2, user={"login": "codecov[bot]", "type": "Bot"})
        with TemporaryDirectory() as directory:
            d = Path(directory)
            only = lambda items: (lambda path: items if "/issues/comments" in path else [])
            with patch.object(janitor, "gh_all", side_effect=only([comment, bot])):
                janitor.mojibake(d, "o/r")
            text = (d / "MOJIBAKE.md").read_text(encoding="utf-8")
            self.assertIn("id 1", text)
            self.assertNotIn("id 2", text)
            with patch.object(janitor, "gh_all", side_effect=only([dict(comment, body="Исправлено.")])):
                janitor.mojibake(d, "o/r")
            self.assertFalse((d / "MOJIBAKE.md").exists())


if __name__ == "__main__":
    unittest.main()
