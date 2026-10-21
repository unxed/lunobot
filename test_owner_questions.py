"""Гейт уведомлений владельцу: пропускаются только вопросы."""

import json
import tempfile
import unittest
from pathlib import Path
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


class TriageStateRepoMatchTest(unittest.TestCase):
    def test_tv_does_not_match_tv3_passport(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            projects = root / "projects"
            tv3 = projects / "tv3"
            tv = projects / "tv"
            tv3.mkdir(parents=True)
            tv.mkdir()
            (tv3 / "PROJECT.md").write_text("- Код: https://github.com/unxed/tv3\n")
            (tv3 / "TRIAGE.md").write_text("| 1 | 5 | свободен | 1 | 2026-10-15T00:00:00Z |\n")
            (tv / "PROJECT.md").write_text("- Код: https://github.com/unxed/tv\n")
            (tv / "TRIAGE.md").write_text("| 1 | 5 | ждёт ответа | 5 | 2026-10-15T23:28:02Z |\n")

            with patch.object(oq, "ROOT", root), patch.object(
                    Path, "glob", return_value=[tv3 / "PROJECT.md", tv / "PROJECT.md"]):
                self.assertEqual(oq.triage_state("unxed/tv", 1), "ждёт ответа")


    def test_mention_in_other_passport_text_is_not_a_match(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dn = root / "projects" / "dn"
            tv3 = root / "projects" / "tv3"
            dn.mkdir(parents=True)
            tv3.mkdir()
            (dn / "PROJECT.md").write_text(
                "- Код: https://github.com/unxed/dn\n- Зависимости: submodule [unxed/tv3](https://github.com/unxed/tv3);\n")
            (dn / "TRIAGE.md").write_text("| 1 | 5 | проверяют | 1 | 2026-10-15T00:00:00Z |\n")
            (tv3 / "PROJECT.md").write_text("- Код: https://github.com/unxed/tv3 (Free Pascal)\n")
            (tv3 / "TRIAGE.md").write_text("| 1 | 5 | ждёт ответа | 5 | 2026-10-15T23:28:02Z |\n")

            with patch.object(oq, "ROOT", root), patch.object(
                    Path, "glob", return_value=[dn / "PROJECT.md", tv3 / "PROJECT.md"]):
                self.assertEqual(oq.triage_state("unxed/tv3", 1), "ждёт ответа")


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

    def test_rights_question_passes(self):
        # account-241 (unxed/vtui#207) и account-231 (blue-panels/mcommander#418), 21-10-2026: § 3 п. 13
        # разрешает вопрос о правах, а гейт отклонял любое упоминание токена, прав или 403.
        self.assertIsNone(oq.check_question(
            "Блокирует unxed/vtui#207: токен бота не пишет в unxed/gogpu (Permission denied); "
            "добавить ли unxed/gogpu в токен бота?"))
        self.assertIsNone(oq.check_question(
            "Блокирует blue-panels/mcommander#418: токен бота не комментирует там (403); "
            "дадите ли права или опубликуете ответ ревьюерам сами?"))
        self.assertIsNone(oq.check_question("Не могу запушить ветку в unxed/gogpu: нужен ли боту доступ на push?"))
        self.assertIsNone(oq.check_question("Блокирует PR #5: нет права на запись в форк; нужно ли его выдать боту?"))

    def test_owner_errand_rejected(self):
        # поручение владельцу, а не вопрос (слово владельца 01-10-2026, winget unxed/f4#12)
        self.assertIsNotNone(oq.check_question("Блокирует unxed/vtui#207: выдайте боту доступ к unxed/gogpu?"))
        self.assertIsNotNone(oq.check_question("Блокирует winget: откройте PR в microsoft/winget-pkgs?"))
        self.assertIsNotNone(oq.check_question("Блокирует unxed/f4#12: подпишете ли CLA?"))
        self.assertIsNotNone(oq.check_question("Блокирует PR #7: создадите ли его вручную?"))

    def test_work_question_with_access_words_rejected(self):
        # review unxed/lunobot#246: «запись в», «доступ» вне прав бота не делают вопрос о работе вопросом о правах
        self.assertIsNotNone(oq.check_question("Блокирует unxed/f4#5: нужно ли добавить запись в CHANGELOG?"))
        self.assertIsNotNone(oq.check_question("Блокирует PR #5: стоит ли сделать запись в README о сборке?"))
        self.assertIsNotNone(oq.check_question("Блокирует PR #5: нужно ли покрыть тестами доступ к меню?"))

    def test_rights_without_question_or_blocker_rejected(self):
        self.assertIsNotNone(oq.check_question("Блокирует unxed/vtui#207: нужен доступ к unxed/gogpu."))
        self.assertIsNotNone(oq.check_question("Нужен ли боту доступ на push в unxed/gogpu?"))
        self.assertIsNotNone(oq.check_question("Готово: токен бота не пишет в unxed/gogpu, добавить ли его?"))
        self.assertIsNotNone(oq.check_question("Блокирует PR #5: токен бота не видит лицензию; какая лицензия у HX?"))

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
