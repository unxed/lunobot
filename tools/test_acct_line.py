import io
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr

import acct_line

SIGN = "Лунобот-1 (node 19d368003c6c048e43dbec70; LNX)"
HEAD = "# Захваты\n\nПояснение.\n"
LINE = ("14-10-2026 07:29:56 Я Лунобот-1 (node 19d368003c6c048e43dbec70; LNX; воркер ac9e178c), "
        "взял задачу https://github.com/unxed/dn/issues/{} [pr]")
ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
           GIT_COMMITTER_EMAIL="t@t", GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")


def sh(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, env=ENV, check=True, capture_output=True,
                          text=True, encoding="utf-8").stdout


class AcctLineGitTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = self.tmp.name
        self.bare = os.path.join(t, "bare.git")
        sh(t, "init", "-q", "--bare", "-b", "main", self.bare)
        self.a, self.b = os.path.join(t, "a"), os.path.join(t, "b")
        sh(t, "clone", "-q", self.bare, self.a)
        os.makedirs(os.path.join(self.a, "projects", "dn"))
        self.write(self.a, HEAD)
        sh(self.a, "add", ".")
        sh(self.a, "commit", "-q", "-m", "init")
        sh(self.a, "push", "-q", "origin", "HEAD:main")
        sh(t, "clone", "-q", self.bare, self.b)
        self.env = os.environ.copy()
        os.environ.update(ENV)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.env)
        self.tmp.cleanup()

    def write(self, repo, text):
        with open(os.path.join(repo, "projects/dn/DISPATCH.md"), "w", encoding="utf-8", newline="") as f:
            f.write(text)

    def origin(self):
        return sh(self.a, "--git-dir", self.bare, "show", "main:projects/dn/DISPATCH.md")

    def run_tool(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = acct_line.main([*args, "--repo", self.a])
        return code, out.getvalue() + err.getvalue()

    def test_add_on_stale_clone_with_local_edits_keeps_both(self):
        # другой бот уже запушил строку; клон a отстал и в нём чужая незакоммиченная правка
        self.write(self.b, HEAD + "\n" + LINE.format(1) + "\n")
        sh(self.b, "commit", "-q", "-am", "b")
        sh(self.b, "push", "-q", "origin", "HEAD:main")
        self.write(self.a, "локальный мусор\n")
        code, out = self.run_tool("add", "projects/dn/DISPATCH.md", LINE.format(2), "-m", "dn#2: взял", "--sign", SIGN)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.origin(), HEAD + "\n" + LINE.format(1) + "\n\n" + LINE.format(2) + "\n")
        msg = sh(self.a, "--git-dir", self.bare, "log", "-1", "--format=%B", "main")
        self.assertIn("Lunobot-Instance: " + SIGN, msg)
        files = sh(self.a, "--git-dir", self.bare, "show", "--name-only", "--format=", "main").split()
        self.assertEqual(files, ["projects/dn/DISPATCH.md"])
        with open(os.path.join(self.a, "projects/dn/DISPATCH.md"), encoding="utf-8") as f:
            self.assertEqual(f.read(), "локальный мусор\n")  # рабочая копия не тронута

    def test_push_race_retries_from_fresh_origin(self):
        real, raced = acct_line.git, []

        def racing_git(repo, *args, **kw):
            if args[:1] == ("push",) and not raced:  # другой бот пушит прямо перед нами
                raced.append(1)
                self.write(self.b, HEAD + "\n" + LINE.format(5) + "\n")
                sh(self.b, "commit", "-q", "-am", "b")
                sh(self.b, "push", "-q", "origin", "HEAD:main")
            return real(repo, *args, **kw)

        acct_line.git = racing_git
        try:
            code, out = self.run_tool("add", "projects/dn/DISPATCH.md", LINE.format(6), "-m", "x", "--sign", SIGN)
        finally:
            acct_line.git = real
        self.assertEqual(code, 0, out)
        self.assertIn("пуш отклонён", out)
        self.assertEqual(self.origin(), HEAD + "\n" + LINE.format(5) + "\n\n" + LINE.format(6) + "\n")

    def test_remove_drops_paragraph(self):
        self.write(self.b, HEAD + "\n" + LINE.format(1) + "\n\n" + LINE.format(2) + "\n")
        sh(self.b, "commit", "-q", "-am", "b")
        sh(self.b, "push", "-q", "origin", "HEAD:main")
        code, out = self.run_tool("remove", "projects/dn/DISPATCH.md", "dn/issues/1 ", "-m", "dn#1: снял", "--sign", SIGN)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.origin(), HEAD + "\n" + LINE.format(2) + "\n")

    def test_remove_absent_is_noop(self):
        before = sh(self.a, "--git-dir", self.bare, "rev-parse", "main")
        code, out = self.run_tool("remove", "projects/dn/DISPATCH.md", "issues/99 ", "-m", "x", "--sign", SIGN)
        self.assertEqual(code, 0, out)
        self.assertEqual(sh(self.a, "--git-dir", self.bare, "rev-parse", "main"), before)

    def test_gate_rejects_line_without_route(self):
        before = sh(self.a, "--git-dir", self.bare, "rev-parse", "main")
        bad = LINE.format(3).replace(" [pr]", "")
        code, out = self.run_tool("add", "projects/dn/DISPATCH.md", bad, "-m", "x", "--sign", SIGN)
        self.assertEqual(code, 1, out)
        self.assertIn("ГЕЙТ", out)
        self.assertEqual(sh(self.a, "--git-dir", self.bare, "rev-parse", "main"), before)

    def test_add_refuses_text_without_timestamp(self):
        # 15-10-2026 bbe99226: в DISPATCH.md ушла голая «синхронизация TRIAGE f4» вместо записи
        before = sh(self.a, "--git-dir", self.bare, "rev-parse", "main")
        for bad in ("синхронизация TRIAGE f4", "красный main 72bdcb32", LINE.format(4) + "\n\n" + LINE.format(5)):
            code, out = self.run_tool("add", "projects/dn/DISPATCH.md", bad, "-m", "x", "--sign", SIGN)
            self.assertEqual(code, 1, out)
            self.assertIn("ОТКАЗ", out)
        self.assertEqual(sh(self.a, "--git-dir", self.bare, "rev-parse", "main"), before)

    def test_add_still_takes_record_with_timestamp(self):
        code, out = self.run_tool("add", "projects/dn/DISPATCH.md", LINE.format(6), "-m", "dn#6: взял", "--sign", SIGN)
        self.assertEqual(code, 0, out)
        self.assertIn(LINE.format(6), self.origin())

    def test_sign_without_node_is_refused(self):
        code, out = self.run_tool("add", "projects/dn/DISPATCH.md", LINE.format(4), "-m", "x", "--sign", "Лунобот-1")
        self.assertEqual(code, 2, out)

    def test_sign_with_incomplete_node_identity_is_refused(self):
        for sign in (
            "Лунобот-2 (node 19d368003c6c048e43dbec70; LNX",
            "Лунобот-2 (node 19d368003c6c048e43dbec7z; LNX)",
            "Лунобот-2 (node 19d368003c6c048e43dbec70; UNKNOWN)",
        ):
            with self.subTest(sign=sign):
                code, out = self.run_tool("add", "projects/dn/DISPATCH.md", LINE.format(4), "-m", "x", "--sign", sign)
                self.assertEqual(code, 2, out)

    def test_full_signs_of_all_platforms_and_numbers_are_accepted(self):
        for i, sign in enumerate((
            "Лунобот-1 (node 19d368003c6c048e43dbec70; LNX)",
            "Лунобот-2 (node 19d368003c6c048e43dbec70; MSW)",
            "Лунобот-2 (node 19d368003c6c048e43dbec70; DAR)",
            "Лунобот-2 (node 19d368003c6c048e43dbec70; BSD)",
            "Лунобот-12 (node 19d368003c6c048e43dbec70; LNX)",
        ), start=20):
            with self.subTest(sign=sign):
                code, out = self.run_tool("add", "projects/dn/DISPATCH.md", LINE.format(i), "-m", "x", "--sign", sign)
                self.assertEqual(code, 0, out)


class RemoveLineTest(unittest.TestCase):
    def test_ambiguous_key(self):
        with self.assertRaises(ValueError):
            acct_line.remove_line("a x\n\nb x\n", "x")

    def test_remove_all_hits_in_one_pass(self):
        self.assertEqual(acct_line.remove_line("h\n\na x\n\nb\n\nc x\n", "x", remove_all=True), "h\n\nb\n")
        self.assertIsNone(acct_line.remove_line("h\n", "x", remove_all=True))

    def test_last_paragraph(self):
        self.assertEqual(acct_line.remove_line("h\n\na\n\nb\n", "b"), "h\n\na\n")

    def test_records_only_spares_header(self):
        text = "# Захваты — dn\n\n" + LINE.format(1) + "\n"
        # «dn» есть и в шапке, и в записи: без защиты это была бы неоднозначность, а одна шапка — снесена
        self.assertEqual(acct_line.remove_line(text, "dn", records_only=True), "# Захваты — dn\n")
        self.assertIsNone(acct_line.remove_line("# Захваты — dn\n", "dn", records_only=True))

    def test_remove_legacy_branch_record(self):
        text = "# BRANCHES — bp\n\n15-10-2026 Лунобот-2, ветка `lunobot/pr/old` для https://github.com/unxed/bp/issues/1\n"
        self.assertEqual(
            acct_line.remove_line(text, "lunobot/pr/old", records_only=True, legacy_branch_records=True),
            "# BRANCHES — bp\n",
        )
        self.assertIsNone(
            acct_line.remove_line("# BRANCHES — bp\n", "bp", records_only=True, legacy_branch_records=True)
        )

    def test_legacy_branch_record_does_not_take_dated_header_paragraph(self):
        text = "# BRANCHES — bp\n\n15-10-2026 заметка: ветки bp чистили вручную\n"
        self.assertIsNone(acct_line.remove_line(text, "bp", records_only=True, legacy_branch_records=True))


class UnrecordedHitsTest(unittest.TestCase):
    def test_finds_row_without_seconds(self):
        text = "# CI — dn\n\n19-10-2026 00:15 UTC, тикет x PR pull/151\n\n19-10-2026 00:43:00 Лунобот-1, main\n"
        self.assertEqual(acct_line.unrecorded_hits(text, "pull/151"), [3])
        self.assertIsNone(acct_line.remove_line(text, "pull/151", records_only=True))

    def test_ignores_records_and_headings(self):
        text = "# CI — pull/151\n\n19-10-2026 00:43:00 Лунобот-1, pull/151\n"
        self.assertEqual(acct_line.unrecorded_hits(text, "pull/151"), [])


class GitBytesTest(unittest.TestCase):
    def test_blob_keeps_lf(self):
        # stdin в байтах: "\n" не превращается в os.linesep (CRLF в Windows)
        with tempfile.TemporaryDirectory() as t:
            sh(t, "init", "-q", t)
            blob = acct_line.git(t, "hash-object", "-w", "--stdin", data="а\nб\n").stdout.strip()
            raw = subprocess.run(["git", "-C", t, "cat-file", "blob", blob], capture_output=True).stdout
            self.assertEqual(raw, "а\nб\n".encode("utf-8"))


if __name__ == "__main__":
    unittest.main()
