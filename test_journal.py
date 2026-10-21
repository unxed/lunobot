import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr

import claims
import journal

NODE = "19d368003c6c048e43dbec70"
SIGN1 = f"Лунобот-1 (node {NODE}; LNX)"
SIGN2 = f"Лунобот-2 (node {NODE}; LNX)"
ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
           GIT_COMMITTER_EMAIL="t@t", GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")


def sh(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, env=ENV, check=True, capture_output=True,
                          text=True, encoding="utf-8").stdout


class JournalGitTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = self.tmp.name
        self.bare = os.path.join(t, "bare.git")
        sh(t, "init", "-q", "--bare", "-b", "main", self.bare)
        self.a, self.b = os.path.join(t, "a"), os.path.join(t, "b")
        sh(t, "clone", "-q", self.bare, self.a)
        os.makedirs(os.path.join(self.a, "projects", "f4"))
        with open(os.path.join(self.a, "projects/f4/CI.md"), "w", encoding="utf-8") as f:
            f.write("# CI — f4\n")
        with open(os.path.join(self.a, "OWNER_QUEUE.md"), "w", encoding="utf-8") as f:
            f.write("# Очередь поручений владельца\n")
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
        self.tmp.cleanup()

    def quiet(self, fn, *args, **kw):
        with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()):
            code = fn(*args, **kw)
        return code, out.getvalue()

    def test_add_and_read_back(self):
        rec = {"kind": "reflection", "did": ["unxed/f4#1: land"], "friction": [{"tag": "ci-wait", "text": "ждал quick"}]}
        self.assertEqual(self.quiet(journal.add, self.a, SIGN1, rec)[0], 0)
        got = journal.read(self.b)
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0]["id"], SIGN1)
        self.assertEqual(got[0]["friction"][0]["tag"], "ci-wait")

    def test_reflection_without_friction_list_is_rejected(self):
        code, out = self.quiet(journal.add, self.a, SIGN1, {"kind": "reflection", "did": []})
        self.assertEqual(code, 1)
        self.assertIn("friction", out)

    def test_mojibake_is_rejected(self):
        rec = {"kind": "reflection", "did": [], "friction": [{"tag": "x", "text": "??????? ????? ??????"}]}
        self.assertEqual(self.quiet(journal.add, self.a, SIGN1, rec)[0], 1)

    def test_two_clones_of_one_instance_append_without_loss(self):
        for repo in (self.a, self.b, self.a):
            self.assertEqual(self.quiet(journal.add, repo, SIGN1, {"kind": "round", "round": 1})[0], 0)
        self.assertEqual(len(journal.read(self.a)), 3)

    def test_instances_have_separate_refs(self):
        self.quiet(journal.add, self.a, SIGN1, {"kind": "round"})
        self.quiet(journal.add, self.b, SIGN2, {"kind": "round"})
        refs = sh(self.a, "ls-remote", "origin", "refs/journal/*")
        self.assertIn(f"refs/journal/{NODE}-1", refs)
        self.assertIn(f"refs/journal/{NODE}-2", refs)

    def test_digest_counts_repeated_frictions_and_rounds(self):
        for i in range(2):
            self.quiet(journal.add, self.a, SIGN1, {"kind": "round", "round": i, "runner": "claude", "model": "opus",
                                                    "duration_s": 1200, "cost_usd": 5.0, "exit": 0})
            self.quiet(journal.add, self.a, SIGN1, {"kind": "reflection", "round": i, "did": ["x"],
                                                    "friction": [{"tag": "read-instruction", "text": "долго"}]})
        text = journal.digest(journal.read(self.a))
        self.assertIn("| claude | opus | 2 | 0 | 20 | 10.00 | 5.00 | 2 |", text)
        self.assertIn("**read-instruction** — 2×", text)

    def test_claim_take_and_drop_are_journaled(self):
        line = (f"21-10-2026 12:00:00 Я Лунобот-1 (node {NODE}; LNX; воркер ab12cd34), "
                "взял задачу https://github.com/unxed/f4/issues/7 [land]")
        self.assertEqual(self.quiet(claims.take, self.a, "f4", line)[0], 0)
        self.assertEqual(self.quiet(claims.drop, self.a, "f4", "unxed-f4-7", SIGN1)[0], 0)
        events = [(r["event"], r.get("held_min") is not None) for r in journal.read(self.b, kind="claim")]
        self.assertEqual(events, [("take", False), ("drop", True)])


class RoundTailTest(JournalGitTest):
    def log(self, lines):
        path = os.path.join(self.tmp.name, "round.log")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(json.dumps(x, ensure_ascii=False) for x in lines))
        return path

    def run_round(self, exit_code):
        path = self.log([{"type": "system", "subtype": "init"},
                         {"type": "assistant", "message": {"content": [{"type": "text", "text": "чиню staging"}]}},
                         {"type": "user", "message": {"content": [{"type": "tool_result", "content": "секрет инструмента"}]}},
                         {"type": "result", "num_turns": 3, "total_cost_usd": 1.0, "result": "итог"}])
        self.quiet(journal.main, ["round", path, "--sign", SIGN1, "--runner", "r", "--model", "m",
                                  "--round", "3", "--exit", str(exit_code), "--duration", "60", "--repo", self.a])
        return journal.read(self.b, kind="round")[-1]

    def test_failed_round_keeps_own_words_not_tool_output(self):
        r = self.run_round(124)
        self.assertIn("чиню staging", r["tail"])
        self.assertNotIn("секрет", r["tail"])
        self.assertIn("Неудачные круги", journal.digest([r]))

    def test_good_round_has_no_tail(self):
        self.assertNotIn("tail", self.run_round(0))


class MetricsTest(unittest.TestCase):
    def write(self, text):
        f = tempfile.NamedTemporaryFile("w", delete=False, suffix=".log", encoding="utf-8")
        f.write(text)
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_claude_stream_json(self):
        lines = [{"type": "system", "subtype": "init"},
                 {"type": "assistant", "message": {"usage": {"input_tokens": 3, "output_tokens": 10,
                                                             "cache_read_input_tokens": 100}}},
                 {"type": "result", "num_turns": 30, "total_cost_usd": 4.5, "result": "итог"},
                 {"type": "result", "num_turns": 2, "total_cost_usd": 5.25, "result": "ещё"}]
        m = journal.metrics(self.write("\n".join(json.dumps(x, ensure_ascii=False) for x in lines)))
        self.assertEqual((m["cost_usd"], m["turns"], m["tokens"]["cache_read_input_tokens"]), (5.25, 32, 100))
        self.assertFalse(m["rate_limited"])

    def test_tool_output_mentioning_limits_is_not_a_limit(self):
        m = journal.metrics(self.write("> build\nвывод: rate limit в тексте тикета\nError: usage limit reached\n"),
                            "opencode")
        self.assertTrue(m["rate_limited"])
        m = journal.metrics(self.write("> build\nвывод: rate limit в тексте тикета\n"), "opencode")
        self.assertFalse(m["rate_limited"])


if __name__ == "__main__":
    unittest.main()
