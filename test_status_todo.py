import tempfile
import unittest
from pathlib import Path

import check_triage
import status_todo

TRIAGE = """# TRIAGE — demo

| тикет | приоритет | состояние | комментариев | updatedAt |
| --- | --- | --- | --- | --- |
{rows}
"""


class RemainderTest(unittest.TestCase):
    def test_heading_with_list_skips_done_items(self):
        text = "# t\n\n## Осталось (одна часть за круг)\n1. ✓ сделано\n2. (сделано 15-10) ещё\n3. Ключи очереди по дискам.\n4. Другое.\n\n## Журнал\nx\n"
        self.assertEqual(status_todo.remainder(text), "Ключи очереди по дискам.")

    def test_inline_remainder(self):
        self.assertEqual(status_todo.remainder("Осталось: поднять zipper до тега.\nСостояние: x"), "поднять zipper до тега.")

    def test_uses_latest_remainder_section(self):
        text = "## Осталось\nЧасть 2 уже устарела.\n\n## Дальше\nЧасть 3 — актуальная работа.\n"
        self.assertEqual(status_todo.remainder(text), "Часть 3 — актуальная работа.")

    def test_empty_latest_section_closes_earlier_remainder(self):
        text = "## Осталось\nЧасть 2 уже устарела.\n\n## Дальше\nНичего обязательного — шаги завершены.\n"
        self.assertIsNone(status_todo.remainder(text))

    def test_double_heading_with_slash(self):
        # unxed/f4#1998: «Осталось/Дальше: …» — остаток в той же строке, как у «Осталось: …»
        self.assertEqual(status_todo.remainder("Осталось/Дальше: закрывать диалог.\n\n## Часть 2\nx\n"), "закрывать диалог.")

    def test_inline_with_condition_in_parentheses_reads_next_lines(self):
        text = "Осталось (каждая часть — свой PR):\n2в. Ctrl+F12 — меню.\n3а. Ctrl+H.\n"
        self.assertEqual(status_todo.remainder(text), "Ctrl+F12 — меню.")

    def test_nothing_mandatory_variants_are_skipped(self):
        for body in ("Ничего обязательного, ждём автора.", "Ничего исполнимого. Тикет — кандидат.", "Исполнимых частей нет.",
                     "Нечего делать, пока автор не ответит.", "Необязательное: настройки в окне.",
                     "1. Необязательно: расширение.", "Планового остатка нет.", "только при желании — привязки",
                     "После зелёного поезда — «Пробуйте!» автору.", "«Пробуйте!» дан, ждём."):
            with self.subTest(body=body):
                self.assertIsNone(status_todo.remainder(f"## Осталось\n{body}\n"))
                self.assertIsNone(status_todo.remainder(f"Осталось: {body}\n"))

    def test_heading_condition_skips_section(self):
        for heading in ("Осталось (после ответа автора; до ответа не брать)", "Осталось (только после файлов от автора; до них не брать)",
                        "Осталось (необязательно, по запросу автора)"):
            with self.subTest(heading=heading):
                self.assertIsNone(status_todo.remainder(f"## {heading}\n\nЧасть 2 — что-то сделать.\n"))

    def test_phrase_in_middle_of_a_part_does_not_skip_it(self):
        text = "## Осталось\nЧасть 3 — ключи очереди; необязательно: логи.\n"
        self.assertEqual(status_todo.remainder(text), "Часть 3 — ключи очереди; необязательно: логи.")

    def test_no_section_or_empty_section(self):
        self.assertIsNone(status_todo.remainder("# t\n\nТекст без остатка\n"))
        self.assertIsNone(status_todo.remainder("## Осталось\n\n## Журнал\nx\n"))
        self.assertIsNone(status_todo.remainder("## Осталось\n1. ✓ всё\n"))

    # Тексты ниже — выдержки из реальных status-файлов (projects/dn/status/80.md, projects/f4/status/1998.md).
    DN80 = (
        "## Осталось (одна часть за круг, файл за файлом)\n\n"
        "1. (сделано 17-10-2026: `uucode.pas` влит в unxed/dn#126.)\n"
        "2. Последняя часть: включить сканер в CI со списком допустимых (см. выше), когда остальные перенесены.\n\n"
        "18-10-2026 04:05:54 UTC (Лунобот-2): PR unxed/dn#134 зелёный, но база устарела; PR не влит.\n"
        "Осталось: после освобождения общего слота обновить PR на актуальный main, пройти обязательные проверки и затем влить.\n"
        "18-10-2026 05:54 UTC (Лунобот-1): часть влита (unxed/dn#137). Осталось в `--reads` по `filecopy.pas`: `TryToReset`, `DoSkip`; "
        "затем сканер в CI со списком допустимых.\n\n"
        "18-10-2026 15:02 UTC (Лунобот-2): `TryToReset` перенесён. PR ещё не запускались. "
        "Осталось: после освобождения слота запушить ветку, открыть PR и пройти `dn.yml`.\n")

    def test_dn80_waiting_for_ci_slot_keeps_scanner_part(self):
        # unxed/dn#80: последняя запись — ожидание свободного слота CI; устаревший «обновить PR» не выдаётся
        got = status_todo.remainder(self.DN80)
        self.assertTrue(got.startswith("Последняя часть: включить сканер в CI"), got)
        self.assertIsNone(status_todo.remainder(self.DN80.split("2. Последняя")[0]))  # без общего остатка — нечего выдавать

    F4_1998 = (
        "Часть 1 (приземлена в staging).\n\n"
        "Осталось/Дальше: единые границы «атомарной операции» (квик-вью/F3) при необходимости сбрасывать отказ раньше; проверка на macOS.\n\n"
        "## Часть 6 — отдельные подсчёты должны начинать новый sudo scope\n"
        "18-10-2026 12:24:06 UTC (Лунобот-2): добавлен регрессионный тест; коммит `e6773cdd` в клоне.\n"
        "Осталось/Дальше: запустить sandbox `go test ./vfs/` на точном SHA, затем выполнить `train.py land`.\n"
        "Осталось/Дальше: часть 6 приземлена в staging; она попадёт в main через поезд. Следующая проверка — штатный tick/поезд.\n")

    def test_f4_1998_landed_part_falls_back_to_general_remainder(self):
        # unxed/f4#1998: «приземлена в staging … через поезд» — рутина § 7.2 п. 4, остаток общий
        got = status_todo.remainder(self.F4_1998)
        self.assertTrue(got.startswith("единые границы «атомарной операции»"), got)

    def test_live_part_is_not_lost_and_other_routine_is_unchanged(self):
        # unxed/goWidgets#13: живая «часть 6» остаётся; последняя запись без ожидания рутины побеждает первую
        text = "Осталось: часть 5 — устарела.\n\n## Дальше\nчасть 6 — FastStone UX parity, отдельными шагами по одной возможности.\n"
        self.assertEqual(status_todo.remainder(text), "часть 6 — FastStone UX parity, отдельными шагами по одной возможности.")
        # приземлена, но без «попадёт в main» — как unxed/f4#285 — остаётся выдачей как раньше
        self.assertTrue(status_todo.remainder("Осталось: Часть 3б приземлена (`9de7` в staging). После зелёного поезда — «Пробуйте!».\n"))
        # единственная секция с ожиданием слота — выдавать нечего, а не устаревшее «обновить PR»
        self.assertIsNone(status_todo.remainder("Осталось: после освобождения общего слота обновить PR.\n"))

    def test_short_cuts_long_lines(self):
        got = status_todo.short("а" * 300)
        self.assertEqual(len(got), 160)
        self.assertTrue(got.endswith("…"))
        self.assertEqual(status_todo.short("ab  cd"), "ab cd")


class TodoTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for module in (status_todo, check_triage):
            old = module.ROOT
            module.ROOT = self.root
            self.addCleanup(setattr, module, "ROOT", old)

    def project(self, name, rows, statuses, dispatch=""):
        base = self.root / "projects" / name
        (base / "status").mkdir(parents=True)
        (base / "PROJECT.md").write_text(f"# {name}\nhttps://github.com/unxed/{name}\n", encoding="utf-8")
        (base / "TRIAGE.md").write_text(TRIAGE.format(rows="\n".join(
            f"| {n} | {p} | {s} | 1 | 2026-10-16T00:00:00Z |" for n, p, s in rows)), encoding="utf-8")
        (base / "DISPATCH.md").write_text("# DISPATCH\n\nФайл содержит только действующие захваты.\n" + dispatch, encoding="utf-8")
        for name_, text in statuses.items():
            (base / "status" / name_).write_text(text, encoding="utf-8")

    def test_filters_and_order(self):
        busy = "17-10-2026 07:48:08 Я Лунобот-1 (node 19d368003c6c048e43dbec70; LNX), взял задачу https://github.com/unxed/demo/issues/6 [land]\n"
        self.project("demo", [(5, "5", "проверяют"), (3, "3", "проверяют"), (4, "3", "ждёт ответа"), (6, "1", "проверяют"),
                              (7, "2", "спор"), (8, "2!", "в пути"), (9, "4", "проверяют")], {
            "5.md": "## Осталось\nЧасть 2.\n",
            "3.md": "Осталось: часть 1.\n",
            "4.md": "## Осталось\nЧасть 9.\n",       # ждёт ответа
            "6.md": "## Осталось\nЧасть 4.\n",       # занят в DISPATCH.md
            "7.md": "## Осталось\nЧасть 5.\n",       # спор
            "8.md": "## Осталось\nЧасть 7.\n",       # приоритет «2!» — владельца
            "9.md": "## Осталось\nНичего обязательного.\n",
            "11.md": "## Осталось\nЧасть 8.\n",      # нет в TRIAGE.md — закрыт
            "notes.md": "## Осталось\nне тикет\n",
        }, busy)
        found = sorted(status_todo.todo("demo"))
        self.assertEqual([row[2] for row in found], [8, 3, 5])
        self.assertEqual(found[0][3:], ("unxed/demo#8", "2!, в пути", "Часть 7."))

    def test_main_prints_one_line_per_ticket_and_all_projects(self):
        self.project("aaa", [(1, "5", "проверяют")], {"1.md": "## Осталось\nЧасть 2.\n"})
        self.project("bbb", [(2, "3", "свободен")], {"2.md": "## Осталось\nЧасть 1.\n"})
        import contextlib
        import io
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = status_todo.main(["--all"])
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue().splitlines(),
                         ["unxed/bbb#2 [3, свободен] Часть 1.", "unxed/aaa#1 [5, проверяют] Часть 2."])

    def test_unknown_project_and_bad_args_return_2(self):
        import contextlib
        import io
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(status_todo.main(["nope"]), 2)
            self.assertEqual(status_todo.main([]), 2)
            self.assertEqual(status_todo.main(["--bad"]), 2)
            self.assertEqual(status_todo.main(["a", "b"]), 2)


if __name__ == "__main__":
    unittest.main()
