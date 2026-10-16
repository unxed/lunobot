import unittest

import check_try


class TicketsWithoutTryTest(unittest.TestCase):
    def rows(self):
        return {
            1: {"state": "проверяют"},
            2: {"state": "проверяют"},
            3: {"state": "свободен"},
            4: {"state": "проверяют"},
        }

    def test_finds_only_checking_tickets_without_try(self):
        comments = {
            1: [{"body": "Исправлено.\n\n— Пробуйте!"}],
            2: [{"body": "Лунобот завершил работу, исправление в staging."}],
            3: [],
            4: [{"body": "Please TRY IT now"}, {"body": None}],
        }
        self.assertEqual(check_try.tickets_without_try(self.rows(), lambda n: comments[n]), [2])

    def test_ticket_without_comments_is_missing(self):
        self.assertEqual(check_try.tickets_without_try({5: {"state": "проверяют"}}, lambda n: []), [5])

    def test_promise_in_guillemets_is_not_try(self):
        # комментарий «в staging» из § 9 обещает «Пробуйте!», но им не является
        promise = "Исправлено — войдёт в main со следующим поездом; «Пробуйте!» будет отдельным комментарием."
        self.assertEqual(check_try.tickets_without_try({7: {"state": "проверяют"}}, lambda n: [{"body": promise}]), [7])

    def test_english_and_summary_forms_count(self):
        bodies = ["The snapshot is out. Please try this build.", "Итог: сделано и уже в `main`.", "@nz256, пробуйте! Исправление в main"]
        rows = {n: {"state": "проверяют"} for n in range(10, 13)}
        got = check_try.tickets_without_try(rows, lambda n: [{"body": bodies[n - 10]}])
        self.assertEqual(got, [])

    def test_nothing_to_try_is_not_try(self):
        body = "Step 1 is merged. Nothing to try on your side."
        self.assertEqual(check_try.tickets_without_try({8: {"state": "проверяют"}}, lambda n: [{"body": body}]), [8])

    def test_other_states_are_not_fetched(self):
        def fail(number):
            raise AssertionError("комментарии не должны запрашиваться")
        self.assertEqual(check_try.tickets_without_try({6: {"state": "ждёт ответа"}}, fail), [])


if __name__ == "__main__":
    unittest.main()
