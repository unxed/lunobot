import unittest
from unittest import mock

import train


class ExistingRefTest(unittest.TestCase):
    def test_404_json_is_not_a_ref(self):
        # `gh api` prints the 404 body to stdout; api() parses it into a dict.
        body = {"message": "Not Found", "status": "404"}
        with mock.patch.object(train, "api", return_value=body):
            self.assertIsNone(train.existing_ref("repos/o/r/git/ref/heads/x"))

    def test_empty_answer_is_not_a_ref(self):
        with mock.patch.object(train, "api", return_value=None):
            self.assertIsNone(train.existing_ref("repos/o/r/git/ref/heads/x"))

    def test_real_ref_is_returned(self):
        ref = {"ref": "refs/heads/x", "object": {"sha": "abc"}}
        with mock.patch.object(train, "api", return_value=ref):
            self.assertEqual(train.existing_ref("repos/o/r/git/ref/heads/x"), ref)


class RefCreatedTest(unittest.TestCase):
    def test_422_json_is_not_success(self):
        body = {"message": "Reference already exists", "status": "422"}
        self.assertFalse(train.ref_created(body))

    def test_none_and_empty_are_not_success(self):
        self.assertFalse(train.ref_created(None))
        self.assertFalse(train.ref_created({}))

    def test_created_ref_is_success(self):
        self.assertTrue(train.ref_created({"ref": "refs/heads/x", "object": {"sha": "abc"}}))


class FreezeTest(unittest.TestCase):
    LINE = "30-09-2026 20:20:00 Я Лунобот-1 (node 91d86915909d88ed7991a74c; LNX), объявляю заморозку land проекта f4 до нарезки поезда\n"

    def now(self, hh, mm):
        from datetime import datetime, timezone
        return datetime(2026, 9, 30, hh, mm, 0, tzinfo=timezone.utc)

    def test_fresh_freeze_is_active(self):
        self.assertEqual(train.active_freeze(self.LINE, "f4", self.now(20, 30)), "30-09-2026 20:20:00")

    def test_expired_freeze_is_ignored(self):
        self.assertIsNone(train.active_freeze(self.LINE, "f4", self.now(20, 46)))

    def test_other_project_is_ignored(self):
        self.assertIsNone(train.active_freeze(self.LINE, "vtui", self.now(20, 30)))

    def test_impossible_date_is_ignored(self):
        line = self.LINE.replace("30-09-2026", "31-02-2026")
        self.assertIsNone(train.active_freeze(line, "f4", self.now(20, 30)))

    def test_future_stamp_is_ignored(self):
        self.assertIsNone(train.active_freeze(self.LINE, "f4", self.now(20, 10)))


class VendorHashTest(unittest.TestCase):
    @staticmethod
    def commit(sha, msg, parents=1):
        return {"sha": sha, "commit": {"message": msg}, "parents": [{}] * parents}

    VENDOR = ("build(nix): update vendorHash [ci]\n\nLunobot-Task: vendorhash-autosync\n"
              "Fixes-Staging: https://github.com/o/r/actions/runs/1\n")

    def test_vendorhash_commit_does_not_block_the_cut(self):
        self.assertFalse(train.blocks_cut(self.commit("a", self.VENDOR)))

    def test_real_fix_still_blocks_the_cut(self):
        self.assertTrue(train.blocks_cut(self.commit("a", "fix\n\nFixes-Staging: https://x\n")))
        self.assertTrue(train.blocks_cut(self.commit("a", "revert\n\nStaging-Revert: abc\n")))

    def test_cut_extends_over_directly_following_vendorhash_commits(self):
        after = [self.commit("v1", self.VENDOR), self.commit("v2", self.VENDOR),
                 self.commit("w", "work\n\nTouch: #1\n"), self.commit("v3", self.VENDOR)]
        self.assertEqual(train.extend_over_vendorhash("green", after), "v2")

    def test_cut_stays_when_next_commit_is_not_vendorhash(self):
        after = [self.commit("w", "work\n\nTouch: #1\n"), self.commit("v", self.VENDOR)]
        self.assertEqual(train.extend_over_vendorhash("green", after), "green")


class StagingHealthTest(unittest.TestCase):
    """После красного quick только бот-коммит vendorHash — не «healing» (land не разрешён)."""

    @staticmethod
    def commit(sha, msg):
        return {"sha": sha, "commit": {"message": msg}, "parents": [{}]}

    def health(self, after):
        red = {"conclusion": "failure", "head_sha": "red", "created_at": "2026-01-01T00:00:00Z"}
        with mock.patch.object(train, "api", return_value={"commit": {"sha": "tip"}}), \
                mock.patch.object(train, "quick_runs", return_value=[red]), \
                mock.patch.object(train, "compare", return_value={"commits": after}):
            return train.staging_health("o/r")[0]

    def test_only_a_vendorhash_commit_after_a_red_quick_stays_red(self):
        self.assertEqual(self.health([self.commit("v", VendorHashTest.VENDOR)]), "red")

    def test_a_real_fix_after_a_red_quick_is_healing(self):
        fix = self.commit("f", "fix\n\nFixes-Staging: https://x\n")
        self.assertEqual(self.health([fix]), "healing")

    def test_a_real_fix_next_to_a_vendorhash_commit_is_healing(self):
        after = [self.commit("v", VendorHashTest.VENDOR), self.commit("f", "revert\n\nStaging-Revert: abc\n")]
        self.assertEqual(self.health(after), "healing")

    def test_plain_work_after_a_red_quick_stays_red(self):
        self.assertEqual(self.health([self.commit("w", "work\n\nTouch: #1\n")]), "red")


if __name__ == "__main__":
    unittest.main()
