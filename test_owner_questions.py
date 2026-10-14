"""Гейт уведомлений владельцу: пропускаются только вопросы."""

import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import notify_owner
import owner_questions as oq

URL = "https://github.com/unxed/f4/issues/1#issuecomment-1"


class ApiJsonPaginationTest(unittest.TestCase):
    def test_proxy_link_error_falls_back_to_explicit_pages(self):
        page1 = [{"id": i} for i in range(100)]
        page2 = [{"id": 100}]
        with patch("owner_questions.subprocess.run") as run:
            run.side_effect = [
                SimpleNamespace(returncode=1, stdout="", stderr=(
                    "Numeric-ID repositories/123 paths are not supported through this proxy"
                )),
                SimpleNamespace(returncode=0, stdout=json.dumps(page1), stderr=""),
                SimpleNamespace(returncode=0, stdout=json.dumps(page2), stderr=""),
            ]
            result = oq.api_json("repos/example/project/issues/1/comments?per_page=100")

        self.assertEqual(len(result), 101)
        self.assertEqual(run.call_args_list[1].args[0][-1], "repos/example/project/issues/1/comments?per_page=100&page=1")
        self.assertEqual(run.call_args_list[2].args[0][-1], "repos/example/project/issues/1/comments?per_page=100&page=2")

    def test_non_proxy_error_is_not_mistaken_for_empty_results(self):
        with patch("owner_questions.subprocess.run") as run:
            run.return_value.returncode = 1
            run.return_value.stdout = ""
            run.return_value.stderr = "HTTP 403: forbidden"
            self.assertIsNone(oq.api_json("repos/example/project/comments", check=False))
            self.assertEqual(run.call_count, 1)


class GateTest(unittest.TestCase):
    def test_question_passes(self):
        self.assertIsNone(oq.check_question("Блокирует PR #12: открыть ли его в upstream elfmz/far2l из ветки terminal-dnd-spec?"))
        self.assertIsNone(oq.check_question("Не могу выбрать между двумя схемами ключей: берём общий или раздельные?"))

    def test_self_answerable_rejected(self):
        self.assertIsNotNone(oq.check_question("Блокирует T-05: какая лицензия у HX?"))
        self.assertIsNotNone(oq.check_question("Не могу продолжить: какую версию NC скачать?"))
        self.assertIsNotNone(oq.check_question("Блокирует тест: нужно ли делать очевидное?"))
        self.assertIsNotNone(oq.check_question("Не могу выбрать: добавить ли минимальный браузерный smoke-контракт для Init?"))
        self.assertIsNotNone(oq.check_question("Не могу выбрать: сделать ли 0 значением по умолчанию?"))
        self.assertIsNone(oq.check_question("Блокирует PR #5: применять ли стопку PR в порядке из комментария?"))

    def test_no_blocker_rejected(self):
        self.assertIsNotNone(oq.check_question("Открыть ли PR в upstream?"))
        self.assertIsNotNone(oq.check_question("Готов ли бюджет на lite-сборку?"))

    def test_report_rejected(self):
        self.assertIsNotNone(oq.check_question("Готово: ссылки на документацию обновлены."))
        self.assertIsNotNone(oq.check_question("Готово: обновлено, открыть ли PR?"))
        self.assertIsNotNone(oq.check_question("Спека обновлена по замечаниям."))

    def test_long_rejected(self):
        self.assertIsNotNone(oq.check_question("Блокирует: открыть ли " + "очень " * 100 + "PR?"))

    def test_empty_rejected(self):
        self.assertIsNotNone(oq.check_question(""))
        self.assertIsNotNone(oq.check_question("   \n"))

    def test_two_questions_rejected(self):
        self.assertIsNotNone(oq.check_question("Блокирует PR: открыть ли его? Или подождать?"))


class NotifyTest(unittest.TestCase):
    def run_notify(self, text):
        with patch("sys.argv", ["notify_owner.py", URL, "--text", text]), \
                patch("subprocess.run") as run:
            run.return_value.stdout = "ok"
            run.return_value.returncode = 0
            return notify_owner.main(), run.called

    def test_report_not_sent(self):
        self.assertEqual(self.run_notify("Готово: всё сделано."), (2, False))

    def test_empty_not_sent(self):
        self.assertEqual(self.run_notify(""), (2, False))

    def test_question_sent(self):
        self.assertEqual(self.run_notify("Блокирует PR #5: открыть ли его в upstream?"), (0, True))


if __name__ == "__main__":
    unittest.main()
