import os
import subprocess
import tempfile
import unittest

import acct_push


def sh(cwd, *args):
    subprocess.run(["git", "-C", cwd, "-c", "user.name=t", "-c", "user.email=t@t", *args],
                   check=True, capture_output=True)


def commit(cwd, name, text):
    with open(os.path.join(cwd, name), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    sh(cwd, "add", name)
    sh(cwd, "commit", "-q", "-m", f"edit {name}")


class PushRetryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = self.tmp.name
        self.bare = os.path.join(t, "origin.git")
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", self.bare], check=True)
        self.a = os.path.join(t, "a")
        self.b = os.path.join(t, "b")
        subprocess.run(["git", "clone", "-q", self.bare, self.a], check=True, capture_output=True)
        commit(self.a, "base.md", "base\n")
        sh(self.a, "push", "-q", "origin", "HEAD:main")
        sh(self.a, "branch", "-q", "--set-upstream-to=origin/main")
        subprocess.run(["git", "clone", "-q", self.bare, self.b], check=True, capture_output=True)
        self.logs = []

    def tearDown(self):
        self.tmp.cleanup()

    def log(self, s):
        self.logs.append(s)

    def test_push_after_remote_moved(self):
        commit(self.b, "other.md", "x\n")
        sh(self.b, "push", "-q", "origin", "HEAD:main")
        commit(self.a, "mine.md", "y\n")
        self.assertEqual(acct_push.push_with_retry(self.a, 3, sleep=lambda s: None, log=self.log), 0)
        out = subprocess.run(["git", "-C", self.bare, "ls-tree", "--name-only", "main"],
                             capture_output=True, text=True).stdout.split()
        self.assertEqual(sorted(out), ["base.md", "mine.md", "other.md"])

    def test_race_between_pull_and_push_retries(self):
        commit(self.a, "mine.md", "y\n")
        real = acct_push.git
        state = {"raced": False}

        def racing(repo, *args):
            r = real(repo, *args)
            if args[:2] == ("pull", "--rebase") and not state["raced"]:
                state["raced"] = True  # чужой пуш между нашим pull и push
                commit(self.b, "other.md", "x\n")
                sh(self.b, "push", "-q", "origin", "HEAD:main")
            return r

        acct_push.git = racing
        try:
            rc = acct_push.push_with_retry(self.a, 3, sleep=lambda s: None, log=self.log)
        finally:
            acct_push.git = real
        self.assertEqual(rc, 0)
        self.assertTrue(any("отклонён" in s for s in self.logs))
        self.assertTrue(any("запушено (попытка 2)" in s for s in self.logs))

    def test_rebase_conflict_aborts_and_reports(self):
        commit(self.b, "base.md", "theirs\n")
        sh(self.b, "push", "-q", "origin", "HEAD:main")
        commit(self.a, "base.md", "mine\n")
        self.assertEqual(acct_push.push_with_retry(self.a, 3, sleep=lambda s: None, log=self.log), 1)
        self.assertTrue(any("origin целиком" in s for s in self.logs))
        status = subprocess.run(["git", "-C", self.a, "status", "--porcelain"], capture_output=True, text=True).stdout
        self.assertEqual(status.strip(), "")  # rebase прерван, дерево не в конфликте

    def test_nothing_to_push_is_ok(self):
        self.assertEqual(acct_push.push_with_retry(self.a, 2, sleep=lambda s: None, log=self.log), 0)

    def test_dirty_tree_is_usage_error(self):
        with open(os.path.join(self.a, "base.md"), "w", encoding="utf-8") as f:
            f.write("dirty\n")
        self.assertEqual(acct_push.main(["--repo", self.a]), 2)


if __name__ == "__main__":
    unittest.main()
