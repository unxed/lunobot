import io
import os
import subprocess
import tempfile
import time
import unittest
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timedelta, timezone

import claims

NODE = "19d368003c6c048e43dbec70"
OTHER = "801452e4fd3b9a26f8e6f02c"
ME = f"Лунобот-1 (node {NODE}; LNX)"
THEM = f"Лунобот-2 (node {OTHER}; LNX)"
F4 = "https://github.com/unxed/f4/issues/{}"
ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
           GIT_COMMITTER_EMAIL="t@t", GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
def ago(minutes):
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes)).strftime("%d-%m-%Y %H:%M:%S")


TS0 = ago(30)
QUEUE = "# Очередь поручений владельца\n\nАвтор доверенных тикетов: unxed\n\n--\n\n## account-213\nПоручение: x\n"


def line(n, who=ME, tail=" [land]", ts=None, worker=None):
    w = who.replace(")", f"; воркер {worker})") if worker else who
    ts = ts or TS0
    return f"{ts} Я {w}, взял задачу {F4.format(n)}{tail}"


def custom(text, who=ME, route="[urgent: по § 5 п. 2 — красный staging]", ts=None):
    ts = ts or TS0
    return f"{ts} Я {who}, взял кастомную задачу «{text}» по § 5 п. 2 {route}"


def sh(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, env=ENV, check=True, capture_output=True,
                          text=True, encoding="utf-8").stdout


class KeysTest(unittest.TestCase):
    def test_ticket_and_part(self):
        self.assertEqual(claims.keys(line(1602)), ["unxed-f4-1602"])
        self.assertEqual(claims.keys(line(1602, tail=" (часть 3 из 4) [land]")), ["unxed-f4-1602/part-3"])
        self.assertEqual(claims.keys(line(90, tail=" (часть 6в, …) [land]")), ["unxed-f4-90/part-6v"])

    def test_incidents(self):
        self.assertEqual(claims.keys(custom("красный staging f4: TestCopy")), ["staging"])
        self.assertEqual(claims.keys(custom("красный main 68c27d1ab", route="[urgent: по § 5 п. 2 — красный main]")),
                         ["main-68c27d1"])
        self.assertEqual(claims.keys(custom("красный поезд #1968", route="[urgent: по § 5 п. 2 — красный поезд]")),
                         ["train-1968"])
        self.assertEqual(claims.keys(custom("застой main", route="[urgent: по § 5 п. 2 — застой main]")),
                         ["stall-main"])

    def test_queue_block_wins_over_ticket_refs(self):
        text = custom("account-213: шаг 11 unxed/bp#56", route="[urgent: по § 4 п. 1 — поручение владельца]")
        self.assertEqual(claims.keys(text, {"account-213"}), ["queue-account-213"])
        self.assertEqual(claims.keys(text), ["unxed-bp-56"])

    def test_custom_without_refs_is_hashed_and_stable(self):
        a = claims.keys(custom("триаж 900–931", route="[urgent: по § 5 п. 4 — учётный шаг]"))
        b = claims.keys(custom("Триаж  900–931", route="[land]"))
        self.assertEqual(a, b)
        self.assertRegex(a[0], r"^custom-[0-9a-f]{12}$")

    def test_freeze_and_note(self):
        self.assertEqual(claims.keys(f"20-10-2026 10:00:00 Я {ME}, объявляю заморозку land проекта f4 до нарезки"),
                         ["freeze"])
        self.assertEqual(claims.keys(f"20-10-2026 10:00:00 Я {ME}, прекращаю работу: команда владельца"),
                         [f"note-1-{NODE}"])


class GitCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = self.tmp.name
        self.bare = os.path.join(t, "bare.git")
        sh(t, "init", "-q", "--bare", "-b", "main", self.bare)
        self.a, self.b = os.path.join(t, "a"), os.path.join(t, "b")
        sh(t, "clone", "-q", self.bare, self.a)
        os.makedirs(os.path.join(self.a, "projects", "f4"))
        self.put("projects/INDEX.md", "1. [f4](f4/PROJECT.md)\n")
        self.put("projects/f4/DISPATCH.md", "# DISPATCH — f4\n\nФайл содержит только действующие захваты.\n")
        self.put("projects/f4/CI.md", "# CI — f4\n")
        self.put("OWNER_QUEUE.md", QUEUE)
        sh(self.a, "add", ".")
        sh(self.a, "commit", "-q", "-m", "init")
        sh(self.a, "push", "-q", "origin", "HEAD:main")
        sh(t, "clone", "-q", self.bare, self.b)
        self.env = os.environ.copy()
        os.environ.update(ENV)
        claims._fetched.clear()

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.env)
        claims._fetched.clear()
        self.tmp.cleanup()

    def put(self, rel, text, repo=None):
        with open(os.path.join(repo or self.a, rel), "w", encoding="utf-8", newline="") as f:
            f.write(text)

    def quiet(self, fn, *args, **kw):
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(out):
            code = fn(*args, **kw)
        self.out = out.getvalue()
        claims._fetched.clear()
        return code

    def remote_refs(self):
        return sorted(l.split("\t")[1] for l in sh(self.a, "ls-remote", self.bare, "refs/claims/*").splitlines())


class TakeTest(GitCase):
    def test_take_then_other_owner_is_refused(self):
        self.assertEqual(self.quiet(claims.take, self.a, "f4", line(1)), 0)
        self.assertEqual(self.remote_refs(), ["refs/claims/f4/unxed-f4-1"])
        self.assertEqual(self.quiet(claims.take, self.b, "f4", line(1, who=THEM)), 1)
        self.assertIn("занято", self.out)
        self.assertIn(line(1), self.out)

    def test_same_owner_retake_is_noop(self):
        self.quiet(claims.take, self.a, "f4", line(1))
        self.assertEqual(self.quiet(claims.take, self.b, "f4", line(1, ts=ago(25))), 0)
        self.assertIn("уже твоё", self.out)

    def test_other_worker_of_same_node_is_refused(self):
        self.quiet(claims.take, self.a, "f4", line(1, worker="aaaa1111"))
        self.assertEqual(self.quiet(claims.take, self.b, "f4", line(1, worker="bbbb2222")), 1)

    def test_whole_ticket_and_part_conflict_both_ways(self):
        self.assertEqual(self.quiet(claims.take, self.a, "f4", line(5, tail=" (часть 2 из 3) [land]")), 0)
        self.assertEqual(self.quiet(claims.take, self.b, "f4", line(5, who=THEM)), 1)
        self.assertEqual(self.quiet(claims.take, self.b, "f4", line(6, who=THEM)), 0)
        self.assertEqual(self.quiet(claims.take, self.a, "f4", line(6, tail=" (часть 1 из 3) [land]")), 1)

    def test_different_parts_coexist(self):
        self.assertEqual(self.quiet(claims.take, self.a, "f4", line(5, tail=" (часть 2 из 3) [land]")), 0)
        self.assertEqual(self.quiet(claims.take, self.b, "f4", line(5, who=THEM, tail=" (часть 3 из 3) [land]")), 0)

    def test_pair_is_atomic(self):
        self.quiet(claims.take, self.a, "f4", line(7))
        both = (f"{TS0} Я {THEM}, взял кастомную задачу «влить unxed/f4#7 и unxed/f4#8» "
                "по § 5 п. 3 [urgent: по § 5 п. 3 — доводка]")
        self.assertEqual(self.quiet(claims.take, self.b, "f4", both), 1)
        self.assertNotIn("refs/claims/f4/unxed-f4-8", self.remote_refs())

    def test_gate_rejects_line_without_route(self):
        self.assertEqual(self.quiet(claims.take, self.a, "f4", line(1, tail="")), 1)
        self.assertIn("маршрут", self.out)
        self.assertEqual(self.remote_refs(), [])

    def test_ticket_already_in_ci_is_refused_for_land(self):
        self.put("projects/f4/CI.md", "# CI — f4\n\n20-10-2026 09:00:00 Лунобот-1, тикет "
                 f"{F4.format(9)}, PR https://github.com/unxed/f4/pull/10, прогон 1\n")
        sh(self.a, "commit", "-qam", "ci")
        sh(self.a, "push", "-q", "origin", "HEAD:main")
        self.assertEqual(self.quiet(claims.take, self.b, "f4", line(9)), 1)
        self.assertIn("уже в CI.md", self.out)

    def test_queue_block_claim_uses_queue_key(self):
        text = custom("account-213: шаг 11", route="[urgent: по § 4 п. 1 — поручение владельца]")
        self.assertEqual(self.quiet(claims.take, self.a, "f4", text), 0)
        self.assertEqual(self.remote_refs(), ["refs/claims/f4/queue-account-213"])


class LifecycleTest(GitCase):
    def test_records_dedupe_and_keepalive_line(self):
        both = (f"{TS0} Я {ME}, взял кастомную задачу «влить unxed/f4#7 и unxed/f4#8» "
                "по § 5 п. 3 [urgent: по § 5 п. 3 — доводка]")
        self.quiet(claims.take, self.a, "f4", both)
        claims.fetch(self.b)
        self.assertEqual(claims.records(self.b, "f4"), [both])
        self.assertEqual(self.quiet(claims.keepalive, self.b, "f4", "unxed/f4#7", ME), 0)
        claims.fetch(self.b)
        recs = claims.records(self.b, "f4")
        self.assertEqual(recs[0], both)
        self.assertRegex(recs[1], r"Я Лунобот-1 \(node .*\), работаю над кастомной задачей «влить unxed/f4#7")
        # оба ref продлены одним коммитом
        self.assertEqual(len({c["sha"] for c in claims.refs(self.b, "f4")}), 1)

    def test_drop_only_own_unless_foreign_and_stale(self):
        self.quiet(claims.take, self.a, "f4", line(1))
        self.assertEqual(self.quiet(claims.drop, self.b, "f4", "unxed-f4-1", THEM), claims.NOTHING)
        self.assertEqual(self.quiet(claims.drop, self.b, "f4", "unxed-f4-1", THEM, foreign=True), claims.NOTHING)
        self.assertEqual(self.quiet(claims.drop, self.b, "f4", F4.format(1), ME), 0)
        self.assertEqual(self.remote_refs(), [])

    def test_foreign_stale_claim_can_be_picked_up(self):
        old = time.time() - 3 * 3600
        self.quiet(claims.take, self.a, "f4", line(2), unix=old)
        self.assertEqual(self.quiet(claims.drop, self.b, "f4", "unxed-f4-2", THEM, foreign=True), 0)

    def test_drop_ambiguous_needs_all(self):
        self.quiet(claims.take, self.a, "f4", line(1))
        self.quiet(claims.take, self.a, "f4", line(2))
        self.assertEqual(self.quiet(claims.drop, self.b, "f4", "unxed/f4/issues", ME), 1)
        self.assertEqual(self.quiet(claims.drop, self.b, "f4", "unxed/f4/issues", ME, all_=True), 0)

    def test_note_is_overwritten_by_owner(self):
        note = f"{ago(20)} Я {ME}, прекращаю работу: команда владельца"
        later = f"{ago(10)} Я {ME}, прекращаю работу: команда владельца"
        self.assertEqual(self.quiet(claims.take, self.a, "f4", note), 0)
        self.assertEqual(self.quiet(claims.take, self.b, "f4", later), 0)
        claims.fetch(self.a)
        self.assertEqual(claims.records(self.a, "f4"), [later])

    def test_dispatch_text_falls_back_to_file_before_migration(self):
        self.put("projects/f4/DISPATCH.md", "# DISPATCH — f4\n\n" + line(3) + "\n")
        self.assertIn(line(3), claims.dispatch_text(self.a, "f4"))
        self.assertFalse(claims.ref_mode(self.a))


class MigrateTest(GitCase):
    def test_migrate_moves_lines_and_writes_view(self):
        ka = f"{ago(5)} Я {ME}, работаю над задачей {F4.format(4)}"
        self.put("projects/f4/DISPATCH.md", "# DISPATCH — f4\n\nФайл содержит только действующие захваты.\n\n"
                 + "\n\n".join([line(4), ka, line(5, who=THEM)]) + "\n")
        sh(self.a, "commit", "-qam", "claims")
        sh(self.a, "push", "-q", "origin", "HEAD:main")
        self.assertEqual(self.quiet(claims.migrate, self.a, True), 2)
        self.assertEqual(self.remote_refs(), ["refs/claims/f4/unxed-f4-4", "refs/claims/f4/unxed-f4-5"])
        with open(os.path.join(self.a, "projects/f4/DISPATCH.md"), encoding="utf-8") as f:
            view = f.read()
        self.assertIn(claims.MARKER, view)
        self.assertIn(line(4), view)
        self.assertIn(ka, view)  # продление сохранено датой коммиттера
        self.assertTrue(claims.ref_mode(self.a))


class AcctLineRouteTest(GitCase):
    def test_acct_line_delegates_after_migration(self):
        import acct_line
        self.put("projects/f4/DISPATCH.md", claims.render_view("f4", []))
        sh(self.a, "commit", "-qam", "view")
        sh(self.a, "push", "-q", "origin", "HEAD:main")
        before = sh(self.a, "--git-dir", self.bare, "rev-parse", "main")
        code = self.quiet(acct_line.main, ["add", "projects/f4/DISPATCH.md", line(11), "-m", "взял",
                                           "--sign", ME, "--repo", self.b])
        self.assertEqual(code, 0, self.out)
        self.assertEqual(self.remote_refs(), ["refs/claims/f4/unxed-f4-11"])
        self.assertEqual(sh(self.a, "--git-dir", self.bare, "rev-parse", "main"), before)  # main не тронут
        code = self.quiet(acct_line.main, ["remove", "projects/f4/DISPATCH.md", F4.format(11), "-m", "снял",
                                           "--sign", ME, "--repo", self.b])
        self.assertEqual(code, 0, self.out)
        self.assertEqual(self.remote_refs(), [])


class ReleaseAndJanitorTest(GitCase):
    def test_release_drops_own_refs_only(self):
        import release
        self.quiet(claims.take, self.a, "f4", line(1, worker="aaaa1111"))
        self.quiet(claims.take, self.a, "f4", line(2, who=THEM))
        code = self.quiet(release.main, ["--number", "1", "--node", NODE, "--platform", "LNX", "--repo", self.b])
        self.assertEqual(code, 0, self.out)
        self.assertEqual(self.remote_refs(), ["refs/claims/f4/unxed-f4-2"])

    def test_janitor_drops_silent_owner_and_writes_view(self):
        import janitor
        self.quiet(claims.take, self.a, "f4", line(1), unix=time.time() - 3 * 3600)
        self.quiet(claims.take, self.a, "f4", line(2, who=THEM))
        old_root = janitor.ROOT
        janitor.ROOT = type(old_root)(self.b)
        try:
            claims.fetch(self.b)
            now = time.time()
            alive = {("2", OTHER): now}
            self.assertEqual(self.quiet(janitor.sweep_refs, "f4", alive, now), 1)
            claims.fetch(self.b)
            self.assertEqual(janitor.write_views(self.b), 1)
        finally:
            janitor.ROOT = old_root
        self.assertEqual(self.remote_refs(), ["refs/claims/f4/unxed-f4-2"])
        with open(os.path.join(self.b, "projects/f4/DISPATCH.md"), encoding="utf-8") as f:
            view = f.read()
        self.assertIn(line(2, who=THEM), view)
        self.assertNotIn(line(1), view)


if __name__ == "__main__":
    unittest.main()
