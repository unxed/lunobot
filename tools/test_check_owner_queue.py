"""Проверки гейта check_owner_queue.py."""

import unittest

import check_owner_queue as q

HEAD = "# Очередь поручений владельца\n\nАвтор доверенных тикетов: unxed\n\nшапка\n\n--\n\n"
BLOCK = ("## f4-demo-20261016\nЗаметка владельца: текст\nПроект: f4\n"
         "Поручение: сделать\nКритерий: видно\nСостояние: взял в работу — Лунобот-1\n")


class CheckOwnerQueueTest(unittest.TestCase):
    def test_well_formed_file(self):
        self.assertEqual(q.check(HEAD + BLOCK + "\n--\n\nсвободная заметка\n"), [])

    def test_title_glued_to_a_progress_line(self):
        # реальный случай 15-10-2026: строка прогресса дописана в начало без перевода строки
        glued = " 15-10-2026 16:15 UTC (Лунобот-1): готово.# Очередь поручений владельца\n"
        problems = q.check(glued + HEAD.split("\n", 1)[1] + BLOCK)
        self.assertEqual(len(problems), 1)
        self.assertIn("строка 1", problems[0])

    def test_trusted_author_missing_or_after_separator(self):
        self.assertTrue(q.check(HEAD.replace("Автор доверенных тикетов: unxed", "") + BLOCK))
        late = "# Очередь поручений владельца\n\n--\n\nАвтор доверенных тикетов: unxed\n" + BLOCK
        self.assertTrue(any("шапке" in p for p in q.check(late)))

    def test_legacy_block_without_note_is_fine(self):
        self.assertEqual(q.check(HEAD + "## f4-old\nАдресат: Лунобот-1\nПроект: f4\n"), [])

    def test_duplicate_block_id(self):
        problems = q.check(HEAD + BLOCK + "--\n" + BLOCK)
        self.assertEqual(len(problems), 1)
        self.assertIn("повторяет", problems[0])

    def test_crlf_and_replacement_character(self):
        self.assertTrue(any("CR" in p for p in q.check((HEAD + BLOCK).replace("\n", "\r\n"))))
        self.assertTrue(any("U+FFFD" in p for p in q.check(HEAD + BLOCK + "�\n")))


if __name__ == "__main__":
    unittest.main()
