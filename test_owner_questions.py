"""Гейт уведомлений владельцу: пропускаются только вопросы."""

import unittest
from unittest.mock import patch

import notify_owner
import owner_questions as oq

URL = "https://github.com/unxed/f4/issues/1#issuecomment-1"


class GateTest(unittest.TestCase):
    def test_question_passes(self):
        self.assertIsNone(oq.check_question("Открыть ли PR в upstream elfmz/far2l из ветки terminal-dnd-spec?"))
        self.assertIsNone(oq.check_question("Готов ли бюджет на lite-сборку?"))

    def test_report_rejected(self):
        self.assertIsNotNone(oq.check_question("Готово: ссылки на документацию обновлены."))
        self.assertIsNotNone(oq.check_question("Готово: обновлено, открыть ли PR?"))
        self.assertIsNotNone(oq.check_question("Спека обновлена по замечаниям."))

    def test_long_rejected(self):
        self.assertIsNotNone(oq.check_question("Открыть ли " + "очень " * 100 + "PR?"))

    def test_empty_rejected(self):
        self.assertIsNotNone(oq.check_question(""))
        self.assertIsNotNone(oq.check_question("   \n"))

    def test_two_questions_rejected(self):
        self.assertIsNotNone(oq.check_question("Открыть ли PR? Или подождать?"))


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
        self.assertEqual(self.run_notify("Открыть ли PR?"), (0, True))


if __name__ == "__main__":
    unittest.main()
