import datetime
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


class PrematureTryTest(unittest.TestCase):
    NOW = datetime.datetime(2026, 10, 16, 12, 0, tzinfo=datetime.timezone.utc)
    NO_TICKET = "ни в одном из названных коммитов нет этого тикета (чужой коммит?)"

    def run_check(self, rows, comments, in_main, about=None):
        return check_try.premature_tries(rows, lambda n: comments[n], in_main, about, now=self.NOW)

    def row(self, updated="2026-10-16T09:00:00Z"):
        return {"state": "свободен", "updated": updated}

    def test_commit_not_in_main_is_premature(self):
        body = "Исправление в main: https://github.com/unxed/f4/commit/9effe76\n\n— Пробуйте!"
        got = self.run_check({1: self.row()}, {1: [{"body": body}]}, lambda sha: False)
        self.assertEqual(got, [(1, "9effe76", "коммит ещё не в main")])

    def test_unknown_commit_is_reported(self):
        body = "Исправлено: https://github.com/unxed/f4/commit/abc1234f. Пробуйте!"
        got = self.run_check({1: self.row()}, {1: [{"body": body}]}, lambda sha: None)
        self.assertEqual(got, [(1, "abc1234f", "такого коммита нет в репозитории")])

    def test_commit_in_main_is_fine(self):
        body = "Исправлено: https://github.com/unxed/f4/commit/0e58229b — Пробуйте!"
        self.assertEqual(self.run_check({1: self.row()}, {1: [{"body": body}]}, lambda sha: True), [])

    def test_commit_about_another_ticket_is_reported(self):
        body = "Исправление: https://github.com/unxed/f4/commit/9effe76 — Пробуйте!"
        got = self.run_check({1976: self.row()}, {1976: [{"body": body}]}, lambda sha: True,
                             lambda sha, number: False)
        self.assertEqual(got, [(1976, "9effe76", self.NO_TICKET)])

    def two_commits(self, in_main, with_ticket, number=2071):
        body = ("Данные: https://github.com/unxed/f4/commit/67d9ba512 и правка: "
                "https://github.com/unxed/f4/commit/72a596421 — Пробуйте!")
        return self.run_check({number: self.row()}, {number: [{"body": body}]}, in_main,
                              lambda sha, n: sha in with_ticket)

    def test_companion_commit_without_ticket_is_fine(self):
        # unxed/f4#2071: первый коммит шага — «данные» без номера тикета, второй — с `Touch:`
        self.assertEqual(self.two_commits(lambda sha: True, {"72a596421"}), [])
        self.assertEqual(self.two_commits(lambda sha: True, {"67d9ba512"}), [])

    def test_two_commits_without_ticket_are_reported_each(self):
        got = self.two_commits(lambda sha: True, set())
        self.assertEqual(got, [(2071, "67d9ba512", self.NO_TICKET), (2071, "72a596421", self.NO_TICKET)])

    def test_one_of_two_not_in_main_is_reported(self):
        got = self.two_commits(lambda sha: sha == "72a596421", {"72a596421"})
        self.assertEqual(got, [(2071, "67d9ba512", "коммит ещё не в main")])

    def test_one_of_two_unknown_is_reported(self):
        got = self.two_commits(lambda sha: None if sha == "67d9ba512" else True, {"72a596421"})
        self.assertEqual(got, [(2071, "67d9ba512", "такого коммита нет в репозитории")])

    def test_not_in_main_commit_with_ticket_does_not_hide_companion(self):
        # ошибка «не в main» уже названа, лишнюю «чужой коммит» по спутнику не добавляем
        got = self.two_commits(lambda sha: sha == "67d9ba512", {"72a596421"})
        self.assertEqual(got, [(2071, "72a596421", "коммит ещё не в main")])

    def test_ticket_already_returned_to_in_transit_is_quiet(self):
        body = "Исправление: https://github.com/unxed/f4/commit/9effe76 — Пробуйте!"
        row = {"state": "в пути", "updated": "2026-10-16T09:00:00Z"}
        self.assertEqual(self.run_check({1: row}, {1: [{"body": body}]}, lambda sha: False), [])

    def test_mentions_ticket_forms(self):
        yes = ["fix\n\nTouch: #1976", "x (unxed/f4#1976)", "see https://github.com/unxed/f4/issues/1976"]
        no = ["Touch: #19760", "Touch: #1931", "unxed/f4#1976x", "other/repo#1976"]
        for message in yes:
            self.assertTrue(check_try.commit_mentions_ticket(message, "unxed/f4", 1976), message)
        for message in no:
            self.assertFalse(check_try.commit_mentions_ticket(message, "unxed/f4", 1976), message)

    def test_old_ticket_is_not_fetched(self):
        def fail(number):
            raise AssertionError("старый тикет не запрашивается")
        got = check_try.premature_tries({1: self.row("2026-10-01T00:00:00Z")}, fail, lambda sha: False, now=self.NOW)
        self.assertEqual(got, [])

    def test_only_the_last_try_counts(self):
        comments = {1: [{"body": "Было: commit/aaaaaaa1 Пробуйте!"}, {"body": "Теперь commit/bbbbbbb2 Пробуйте!"}]}
        got = self.run_check({1: self.row()}, comments, lambda sha: sha == "bbbbbbb2")
        self.assertEqual(got, [])

    def test_node_ids_versions_and_numbers_are_not_commits(self):
        body = ("Ваша сборка 44c61e9 старше. deadbeef 12345678\n\n"
                "*Лунобот-1 (node 19d368003c6c048e43dbec70; LNX; Claude Sonnet 5.5)* — Пробуйте!")
        self.assertEqual(check_try.commit_refs(body), [])

    def test_commit_of_another_repository_is_not_checked(self):
        # unxed/f4#1610: исправление лежит в unxed/wayland (ветка master); по f4 такого sha нет.
        body = "Исправлено: https://github.com/unxed/wayland/commit/fa6821d8 — Пробуйте!"
        def fail(sha):
            raise AssertionError("чужой репозиторий не запрашивается")
        got = check_try.premature_tries({1: self.row()}, lambda n: [{"body": body}], fail, now=self.NOW,
                                        repo="unxed/f4")
        self.assertEqual(got, [])
        own = body.replace("unxed/wayland", "unxed/f4")
        got = check_try.premature_tries({1: self.row()}, lambda n: [{"body": own}], lambda sha: False,
                                        now=self.NOW, repo="unxed/f4")
        self.assertEqual(got, [(1, "fa6821d8", "коммит ещё не в main")])

    def test_comment_without_try_is_ignored(self):
        body = "Исправление лежит в commit/aaaaaaa1, войдёт в main поездом."
        self.assertEqual(self.run_check({1: self.row()}, {1: [{"body": body}]}, lambda sha: False), [])


if __name__ == "__main__":
    unittest.main()
