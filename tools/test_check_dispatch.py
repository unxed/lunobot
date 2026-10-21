"""Проверки гейта check_dispatch.py: владелец захвата, пересечение ссылок, повтор строки CI.md."""

import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import check_dispatch

NODE = "19d368003c6c048e43dbec70"
URL = "https://github.com/unxed/dn/issues/40"


def line(ts, num, verb="взял", suffix="; LNX", node=NODE, tail=" [pr]"):
    return f"{ts} Я Лунобот-{num} (node {node}{suffix}), {verb} задачу {URL}{tail}"


class MalformedMessageTest(unittest.TestCase):
    def problems(self, text):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "DISPATCH.md")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("# DISPATCH\n\n" + text + "\n")
            return check_dispatch.check(path, 45)[1]

    def test_model_name_in_id_names_the_cause_and_not_the_part(self):
        # 15-10-2026: the id with a model name was rejected as "id не по формату, не указана часть"; the part is optional
        found = self.problems(f"15-10-2026 05:00:54 Я Лунобот-1 (node {NODE}; LNX; Claude Sonnet 5.5), взял задачу {URL} [pr]")
        self.assertEqual([p[0] for p in found], ["формат"])
        self.assertIn("без имени модели", found[0][2])
        self.assertNotIn("не указана часть", found[0][2])


class FutureTimestampTest(unittest.TestCase):
    def test_future_capture_timestamp_is_rejected(self):
        future = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%d-%m-%Y %H:%M:%S")
        found = kinds([line(future, 2)])
        self.assertIn("время", found)


class SameNodeDuplicateTest(unittest.TestCase):
    def problems(self, *lines):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "DISPATCH.md")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("# DISPATCH\n\n" + "\n\n".join(lines) + "\n")
            return check_dispatch.check(path, 45)[1]

    def test_other_number_same_node_is_duplicate(self):
        found = self.problems(line("14-10-2026 16:12:49", 2), line("14-10-2026 16:16:13", 1))
        self.assertEqual([p[0] for p in found], ["дубль"])

    def test_other_number_over_foreign_keepalive_is_duplicate(self):
        found = self.problems(line("14-10-2026 16:12:49", 2),
                              line("14-10-2026 16:14:00", 2, verb="работаю", tail=""),
                              line("14-10-2026 16:16:13", 1))
        self.assertEqual([p[0] for p in found], ["дубль"])

    def test_rewritten_under_new_number_is_not_duplicate(self):
        found = self.problems(line("14-10-2026 16:16:13", 1), line("14-10-2026 16:17:00", 1, verb="работаю", tail=""))
        self.assertEqual(found, [])

    def test_same_number_keepalive_is_not_duplicate(self):
        found = self.problems(line("14-10-2026 16:12:49", 1),
                              line("14-10-2026 16:16:13", 1, verb="работаю", tail=""))
        self.assertEqual(found, [])

    def test_other_node_is_race_not_duplicate(self):
        found = self.problems(line("14-10-2026 16:12:49", 2, node="801452e4fd3b9a26f8e6f02c"),
                              line("14-10-2026 16:16:13", 1))
        self.assertEqual([p[0] for p in found], ["гонка"])


OTHER = "801452e4fd3b9a26f8e6f02c"
HEAD = "# DISPATCH — dn\n\n"


def kinds(dispatch, ci=""):
    with tempfile.TemporaryDirectory() as directory:
        project = Path(directory, "projects", "dn")
        project.mkdir(parents=True)
        path = project / "DISPATCH.md"
        path.write_text(HEAD + "\n\n".join(dispatch) + "\n", encoding="utf-8")
        if ci:
            (project / "CI.md").write_text("# CI — dn\n\n" + ci + "\n", encoding="utf-8")
        _, problems = check_dispatch.check(str(path), 45)
    return [kind for kind, _, _ in problems]


class OwnerTest(unittest.TestCase):
    def test_two_numbers_on_one_node_are_different_owners(self):
        found = kinds([
            f"14-10-2026 08:37:22 Я Лунобот-2 (node {NODE}; LNX), взял задачу "
            "https://github.com/unxed/dn/issues/33 (часть 3 из 4) [pr]",
            f"14-10-2026 08:37:54 Я Лунобот-1 (node {NODE}; LNX; воркер a75b78fc), взял задачу "
            "https://github.com/unxed/dn/issues/33 (часть 3 из 4) [pr]"])
        self.assertIn("дубль", found)  # на узле main уже ловит это как «дубль»

    def test_lettered_part_is_a_part_of_its_own(self):
        # 17-10-2026: «часть 5в» и «часть 5» одного тикета у двух узлов давали ложную «гонку»
        other = "801452e4fd3b9a26f8e6f02c"
        url = "https://github.com/unxed/dn/issues/37"
        found = kinds([
            f"17-10-2026 00:39:16 Я Лунобот-1 (node {other}; LNX), взял задачу {url} "
            "(часть 5в, Ctrl+\\ в корень) [land]",
            f"17-10-2026 00:56:37 Я Лунобот-1 (node {NODE}; LNX), взял задачу {url} "
            "(часть 5, тесты) [land]"])
        self.assertNotIn("гонка", found)
        self.assertNotIn("пересечение", found)

    def test_same_lettered_part_on_two_nodes_is_still_a_race(self):
        other = "801452e4fd3b9a26f8e6f02c"
        url = "https://github.com/unxed/dn/issues/37"
        found = kinds([
            f"17-10-2026 00:39:16 Я Лунобот-1 (node {other}; LNX), взял задачу {url} "
            "(часть 5в, Ctrl+\\ в корень) [land]",
            f"17-10-2026 00:56:37 Я Лунобот-1 (node {NODE}; LNX), взял задачу {url} "
            "(часть 5в, Ctrl+\\ в корень) [land]"])
        self.assertIn("гонка", found)

    def test_part_with_and_without_total_is_the_same_part(self):
        # «часть 3 из 4» и «часть 3» — одна часть: пересечение не должно пропадать из-за разной записи
        other = "801452e4fd3b9a26f8e6f02c"
        url = "https://github.com/unxed/dn/issues/37"
        found = kinds([
            f"17-10-2026 00:39:16 Я Лунобот-1 (node {other}; LNX), взял задачу {url} (часть 3 из 4) [land]",
            f"17-10-2026 00:56:37 Я Лунобот-1 (node {NODE}; LNX), взял задачу {url} (часть 3, тесты) [land]"])
        self.assertIn("пересечение", found)

    def test_bare_part_words_in_free_text_are_not_a_part(self):
        # «часть 2 PR» в тексте кастомной задачи и «часть 2ой» — не часть: сравнение частей не отключается
        other = "801452e4fd3b9a26f8e6f02c"
        url = "https://github.com/unxed/dn/issues/37"
        found = kinds([
            f"17-10-2026 00:39:16 Я Лунобот-1 (node {other}; LNX), взял задачу {url} (часть 3 из 4) [land]",
            f"17-10-2026 00:56:37 Я Лунобот-1 (node {NODE}; LNX), взял задачу {url} "
            "(доводка: часть 2 PR) [land]"])
        self.assertIn("пересечение", found)

    def test_same_session_keepalive_is_not_a_race(self):
        found = kinds([
            f"14-10-2026 08:37:22 Я Лунобот-1 (node {NODE}; LNX), взял задачу "
            "https://github.com/unxed/dn/issues/33 [pr]",
            f"14-10-2026 08:40:00 Я Лунобот-1 (node {NODE}; LNX), работаю над задачей "
            "https://github.com/unxed/dn/issues/33"])
        self.assertEqual(found, [])

    def test_rejects_unrecognized_nonempty_lines(self):
        found = kinds(["взял задачу https://github.com/unxed/dn/issues/40 [land]"])
        self.assertIn("формат", found)

    def test_rejects_unrecognized_record_without_url_or_route(self):
        found = kinds(["взял кастомную задачу «триаж 1929–1929» по § 5 п. 4"])
        self.assertIn("формат", found)

    def test_file_header_text_is_not_malformed(self):
        found = kinds(["Файл содержит только действующие захваты. Формат — § 8 инструкции.\n"
                       "Закончил шаг — удали свои строки, а не дописывай отчёт."])
        self.assertEqual(found, [])


class OverlapTest(unittest.TestCase):
    def test_custom_task_and_url_for_same_ticket_overlap(self):
        # 14-10-2026: «влить зелёный PR #49, unxed/dn#33 часть 3 из 4» и захват URL того же тикета
        found = kinds([
            f"14-10-2026 08:37:22 Я Лунобот-2 (node {NODE}; LNX), взял кастомную задачу "
            "«влить зелёный PR #49, unxed/dn#33 часть 3 из 4» по § 5 п. 3 "
            "[urgent: по § 5 п. 3 — доводка созревшей строки CI.md]",
            f"14-10-2026 08:37:54 Я Лунобот-1 (node {NODE}; LNX; воркер a75b78fc), взял задачу "
            "https://github.com/unxed/dn/issues/33 (часть 3 из 4) [pr]"])
        self.assertIn("пересечение", found)

    def test_same_red_train_taken_twice_overlaps(self):
        # 15-10-2026: красный поезд #1968 взяли Лунобот-1 и Лунобот-2 одного узла с разным текстом задачи
        found = kinds([
            f"15-10-2026 19:52:19 Я Лунобот-1 (node {NODE}; LNX), взял кастомную задачу "
            "«красный поезд #1968: vendorHash после Staging-Revert» по § 5 п. 2 "
            "[urgent: по § 5 п. 2 — красный поезд]",
            f"15-10-2026 19:53:17 Я Лунобот-2 (node {NODE}; LNX), взял кастомную задачу "
            "«красный поезд #1968» по § 5 п. 2 [urgent: по § 5 п. 2 — красный поезд]"])
        self.assertIn("пересечение", found)

    def test_red_staging_taken_by_two_runners_overlaps(self):
        # раннеры Лунобота-1 и Лунобота-2 начинают круг вместе и оба видят красный quick
        found = kinds([
            f"21-10-2026 12:00:10 Я Лунобот-1 (node {NODE}; LNX; воркер a1b2c3d4), взял кастомную задачу "
            "«красный staging f4: TestCopy» по § 5 п. 2 [urgent: по § 5 п. 2 — красный staging]",
            f"21-10-2026 12:00:40 Я Лунобот-2 (node {NODE}; LNX; воркер e5f6a7b8), взял кастомную задачу "
            "«красный quick на lunobot/staging» по § 5 п. 2 [urgent: по § 5 п. 2 — красный quick]"])
        self.assertIn("пересечение", found)

    def test_main_stall_taken_twice_overlaps(self):
        found = kinds([
            f"21-10-2026 12:00:10 Я Лунобот-1 (node {NODE}; LNX), взял кастомную задачу "
            "«застой main f4» по § 5 п. 2 [urgent: по § 5 п. 2 — застой main]",
            f"21-10-2026 12:00:40 Я Лунобот-1 (node {OTHER}; LNX), взял кастомную задачу "
            "«застой main: поезд #2121 не влит» по § 5 п. 2 [urgent: по § 5 п. 2 — застой main]"])
        self.assertIn("пересечение", found)

    def test_red_main_of_different_commits_does_not_overlap(self):
        found = kinds([
            f"15-10-2026 19:21:20 Я Лунобот-2 (node {NODE}; LNX), взял кастомную задачу "
            "«красный main d5f1ef202» по § 5 п. 2 [urgent: по § 5 п. 2 — красный main]",
            f"15-10-2026 19:53:17 Я Лунобот-1 (node {NODE}; LNX), взял кастомную задачу "
            "«красный main 68c27d1» по § 5 п. 2 [urgent: по § 5 п. 2 — красный main]"])
        self.assertNotIn("пересечение", found)

    def test_different_explicit_parts_do_not_overlap(self):
        found = kinds([
            f"14-10-2026 08:37:22 Я Лунобот-2 (node {OTHER}; LNX), взял кастомную задачу "
            "«влить PR unxed/dn#49, unxed/dn#33 часть 2 из 4» по § 5 п. 3 "
            "[urgent: по § 5 п. 3 — доводка созревшей строки CI.md]",
            f"14-10-2026 08:37:54 Я Лунобот-1 (node {NODE}; LNX), взял задачу "
            "https://github.com/unxed/dn/issues/33 (часть 3 из 4) [pr]"])
        self.assertNotIn("пересечение", found)

    def test_one_workers_lines_do_not_overlap_with_itself(self):
        found = kinds([
            f"14-10-2026 08:37:22 Я Лунобот-1 (node {NODE}; LNX; воркер aec573a8), взял "
            "кастомную задачу «довести unxed/dn#54» по § 6 [pr]",
            f"14-10-2026 08:37:54 Я Лунобот-1 (node {NODE}; LNX; воркер aec573a8), взял задачу "
            "https://github.com/unxed/dn/issues/52 (unxed/dn#54) [pr]"])
        self.assertNotIn("пересечение", found)


class CiTest(unittest.TestCase):
    CI = (f"14-10-2026 08:11:41 Лунобот-1 (node {NODE}; LNX), тикет "
          "https://github.com/unxed/dn/issues/52, PR [#54](https://github.com/unxed/dn/pull/54), "
          "коммит `abc1234`, прогон [#1](https://github.com/unxed/dn/actions/runs/1)")

    def test_routine_claim_of_ticket_in_ci_is_rejected(self):
        found = kinds([f"14-10-2026 08:14:27 Я Лунобот-1 (node {OTHER}; LNX), взял задачу "
                       "https://github.com/unxed/dn/issues/52 [pr]"], self.CI)
        self.assertIn("уже в CI.md", found)

    def test_urgent_follow_up_of_ci_line_is_allowed(self):
        found = kinds([f"14-10-2026 08:14:27 Я Лунобот-1 (node {OTHER}; LNX), взял задачу "
                       "https://github.com/unxed/dn/issues/52 "
                       "[urgent: по § 5 п. 3 — доводка созревшей строки CI.md]"], self.CI)
        self.assertNotIn("уже в CI.md", found)

    def test_next_part_of_multipart_ticket_is_allowed(self):
        ci = self.CI.replace("issues/52,", "issues/52 (часть 4 из 6),")
        found = kinds([f"14-10-2026 08:14:27 Я Лунобот-1 (node {OTHER}; LNX), взял задачу "
                       "https://github.com/unxed/dn/issues/52 (часть 5 из 6) [pr]"], ci)
        self.assertNotIn("уже в CI.md", found)

    def test_step_word_is_a_part_too(self):
        # 17-10-2026: захват unxed/bp#27 «(шаг 2 из 3: …)» при «часть 2 из 3» в CI.md гейт не остановил
        ci = self.CI.replace("issues/52,", "issues/52 (часть 2 из 3),")
        found = kinds([f"14-10-2026 08:14:27 Я Лунобот-1 (node {OTHER}; LNX), взял задачу "
                       "https://github.com/unxed/dn/issues/52 (шаг 2 из 3: workflow) [pr]"], ci)
        self.assertIn("уже в CI.md", found)
        found = kinds([f"14-10-2026 08:14:27 Я Лунобот-1 (node {OTHER}; LNX), взял задачу "
                       "https://github.com/unxed/dn/issues/52 (шаг 3 из 3: документация) [pr]"], ci)
        self.assertNotIn("уже в CI.md", found)


class StrayAddedLineTest(unittest.TestCase):
    def stray(self, text):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "DISPATCH.md")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
            return check_dispatch.stray_lines(path)

    def test_loose_text_is_stray(self):
        # 15-10-2026 33247407: «красный main 72bdcb32» вписан руками мимо acct_line.py
        found = self.stray("# DISPATCH — f4\n\n" + line("15-10-2026 10:55:00", 2, tail=" [land]") + "\n\nкрасный main 72bdcb32\n")
        self.assertEqual(list(found.values()), ["красный main 72bdcb32"])

    def test_legal_content_is_not_stray(self):
        text = ("# DISPATCH — f4\n\n"
                "Файл содержит только действующие захваты. Формат — § 8 инструкции.\n"
                "Закончил шаг — удали свои строки, а не дописывай отчёт.\n\n"
                + line("15-10-2026 10:55:00", 2, tail=" [land]") + "\n\n"
                + line("15-10-2026 11:05:00", 2, verb="работаю", tail="") + "\n\n"
                f"15-10-2026 11:10:00 Я Лунобот-2 (node {NODE}; LNX), объявляю заморозку land проекта f4 до нарезки поезда\n\n"
                f"15-10-2026 11:20:00 Я Лунобот-2 (node {NODE}; LNX), прекращаю работу: команда владельца\n")
        self.assertEqual(self.stray(text), {})

    def test_only_added_mode_reports_it(self):
        # полный режим (main без --added-only) этих строк не ищет: он вызывает только check()
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "DISPATCH.md")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("# DISPATCH — f4\n\nкрасный main 72bdcb32\n")
            self.assertEqual(check_dispatch.check(path, 45)[1], [])
            self.assertEqual(list(check_dispatch.stray_lines(path)), [3])


if __name__ == "__main__":
    unittest.main()
