import io
import os
import re
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr

import release

NODE = "19d368003c6c048e43dbec70"
OTHER = "a721a6d1487257292ae00780"
HEAD = "# DISPATCH — dn\n\nФайл содержит только действующие захваты.\n"
MINE = (f"21-10-2026 12:18:44 Я Лунобот-1 (node {NODE}; LNX; воркер afd7ee5e), "
        "взял задачу https://github.com/unxed/dn/issues/90 [land]")
MINE_KEEPALIVE = (f"21-10-2026 12:48:44 Я Лунобот-1 (node {NODE}; LNX), "
                  "работаю над задачей https://github.com/unxed/dn/issues/90")
NUM2 = (f"21-10-2026 12:20:00 Я Лунобот-2 (node {NODE}; LNX), "
        "взял задачу https://github.com/unxed/dn/issues/91 [land]")
OTHER_NODE = (f"21-10-2026 12:21:00 Я Лунобот-1 (node {OTHER}; LNX), "
              "взял задачу https://github.com/unxed/dn/issues/92 [land]")
QUEUE = (
    "# Очередь поручений владельца\n\nАвтор доверенных тикетов: unxed\n\n--\n\n"
    "## account-1\nПоручение: раз\n"
    f"Состояние: взял в работу — Лунобот-1 (node {NODE}; LNX; воркер afd7ee5e), 21-10-2026 12:00:00 UTC\n"
    "Прогресс 21-10-2026 12:10:00 UTC (Лунобот-1): шаг 1\n\n--\n\n"
    "## account-2\nПоручение: два\n"
    f"Состояние: взял в работу — Лунобот-2 (node {NODE}; LNX), 21-10-2026 12:00:00 UTC\n\n--\n\n"
    "## account-3\nПоручение: три\n"
    f"Состояние: ждёт владельца — вопрос; Лунобот-1 (node {NODE}; LNX), 21-10-2026 12:00:00 UTC\n"
)
ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
           GIT_COMMITTER_EMAIL="t@t", GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")


def sh(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, env=ENV, check=True, capture_output=True,
                          text=True, encoding="utf-8").stdout


class PureTest(unittest.TestCase):
    def test_dispatch_drops_only_own_records(self):
        text = "\n\n".join([HEAD.rstrip("\n"), MINE, NUM2, MINE_KEEPALIVE, OTHER_NODE]) + "\n"
        new, gone = release.release_dispatch(text, release.owner(1, NODE))
        self.assertEqual(gone, [MINE, MINE_KEEPALIVE])
        self.assertEqual(new, "\n\n".join([HEAD.rstrip("\n"), NUM2, OTHER_NODE]) + "\n")

    def test_dispatch_without_own_records_is_unchanged(self):
        text = HEAD + "\n" + NUM2 + "\n"
        self.assertEqual(release.release_dispatch(text, release.owner(1, NODE)), (text, []))

    def test_header_mentioning_id_is_not_a_record(self):
        text = HEAD + f"Пример: Я Лунобот-1 (node {NODE}; LNX), взял …\n"
        self.assertEqual(release.release_dispatch(text, release.owner(1, NODE))[1], [])

    def test_queue_frees_only_own_taken_blocks(self):
        new, freed = release.release_queue(QUEUE, release.owner(1, NODE), "Прогресс X: снят")
        self.assertEqual(freed, ["account-1"])
        # прежняя строка следа заменена новой: в блоке одна строка (check_owner_queue.py п. 5)
        self.assertIn("## account-1\nПоручение: раз\nСостояние: свободно\nПрогресс X: снят\n\n--", new)
        self.assertIn("Состояние: взял в работу — Лунобот-2", new)
        self.assertIn("Состояние: ждёт владельца — вопрос; Лунобот-1", new)

    def test_platform_codes(self):
        self.assertEqual([release.platform_code(p) for p in ("linux", "win32", "darwin", "freebsd14")],
                         ["LNX", "MSW", "DAR", "BSD"])


class GitTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = self.tmp.name
        self.bare = os.path.join(t, "bare.git")
        sh(t, "init", "-q", "--bare", "-b", "main", self.bare)
        self.a = os.path.join(t, "a")
        sh(t, "clone", "-q", self.bare, self.a)
        os.makedirs(os.path.join(self.a, "projects", "dn"))
        with open(os.path.join(self.a, "projects/dn/DISPATCH.md"), "w", encoding="utf-8", newline="") as f:
            f.write("\n\n".join([HEAD.rstrip("\n"), MINE, NUM2]) + "\n")
        with open(os.path.join(self.a, "OWNER_QUEUE.md"), "w", encoding="utf-8", newline="") as f:
            f.write(QUEUE)
        sh(self.a, "add", ".")
        sh(self.a, "commit", "-q", "-m", "init")
        sh(self.a, "push", "-q", "origin", "HEAD:main")
        self.env = os.environ.copy()
        os.environ.update(ENV)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.env)
        self.tmp.cleanup()

    def run_tool(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = release.main(["--number", "1", "--node", NODE, "--platform", "LNX",
                                 "--repo", self.a, *args])
        return code, out.getvalue() + err.getvalue()

    def show(self, path):
        return sh(self.a, "--git-dir", self.bare, "show", f"main:{path}")

    def test_release_pushes_one_commit_with_trailer(self):
        code, out = self.run_tool("--reason", "раннер остановлен (Ctrl+C)")
        self.assertEqual(code, 0, out)
        self.assertNotIn("Лунобот-1", self.show("projects/dn/DISPATCH.md"))
        self.assertIn(NUM2, self.show("projects/dn/DISPATCH.md"))
        queue = self.show("OWNER_QUEUE.md")
        self.assertRegex(queue, r"## account-1\nПоручение: раз\nСостояние: свободно\nПрогресс \d\d-\d\d-\d{4} "
                         r"\d\d:\d\d:\d\d UTC \(Лунобот-1 \(node " + NODE + r"; LNX\)\): захват снят — "
                         + re.escape("раннер остановлен (Ctrl+C)"))
        log = sh(self.a, "--git-dir", self.bare, "log", "-1", "--format=%B", "main")
        self.assertIn(f"Lunobot-Instance: Лунобот-1 (node {NODE}; LNX)", log)
        self.assertEqual(sh(self.a, "--git-dir", self.bare, "rev-list", "--count", "main").strip(), "2")

    def test_second_run_is_noop(self):
        self.run_tool()
        code, out = self.run_tool()
        self.assertEqual(code, 0, out)
        self.assertIn("снимать нечего", out)
        self.assertEqual(sh(self.a, "--git-dir", self.bare, "rev-list", "--count", "main").strip(), "2")

    def test_dry_run_pushes_nothing(self):
        code, out = self.run_tool("--dry-run")
        self.assertEqual(code, 0, out)
        self.assertIn("сниму", out)
        self.assertIn(MINE, self.show("projects/dn/DISPATCH.md"))


if __name__ == "__main__":
    unittest.main()
