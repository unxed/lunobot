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


class NightlyStaleTest(unittest.TestCase):
    """nightly_is_stale / should_cancel_main_run: the main run after a fast-forward is kept
    only while the floating nightly of a project that has one is old (or unknown)."""

    def _release(self, hours_old):
        when = train.datetime.now(train.timezone.utc) - train.timedelta(hours=hours_old)
        return {"published_at": when.strftime("%Y-%m-%dT%H:%M:%SZ")}

    def test_project_without_nightly_is_never_stale_and_api_is_not_called(self):
        with mock.patch.object(train, "api") as api:
            self.assertFalse(train.nightly_is_stale("unxed/vtui"))
        api.assert_not_called()

    def test_fresh_nightly_is_not_stale(self):
        with mock.patch.object(train, "api", return_value=self._release(1)):
            self.assertFalse(train.nightly_is_stale("unxed/f4"))

    def test_old_nightly_is_stale(self):
        with mock.patch.object(train, "api", return_value=self._release(train.NIGHTLY_MAX_AGE_H + 1)):
            self.assertTrue(train.nightly_is_stale("unxed/f4"))

    def test_z_suffix_timestamp_is_parsed(self):
        rel = {"published_at": "2020-01-01T00:00:00Z"}
        with mock.patch.object(train, "api", return_value=rel):
            self.assertTrue(train.nightly_is_stale("unxed/f4"))

    def test_404_body_none_and_broken_answers_are_stale_not_a_crash(self):
        for answer in ({"message": "Not Found", "status": "404"}, None, {"published_at": "not a date"}, []):
            with mock.patch.object(train, "api", return_value=answer):
                self.assertTrue(train.nightly_is_stale("unxed/f4"), answer)

    def test_gh_failure_exits_are_caught(self):
        # api() -> run(check=True) ends in sys.exit(); tick must survive it right after the merge.
        with mock.patch.object(train, "api", side_effect=SystemExit("gh api: 502")):
            self.assertTrue(train.nightly_is_stale("unxed/f4"))
        with mock.patch.object(train, "api", side_effect=RuntimeError("boom")):
            self.assertTrue(train.nightly_is_stale("unxed/f4"))

    def test_api_is_called_without_check(self):
        with mock.patch.object(train, "api", return_value=self._release(1)) as api:
            train.nightly_is_stale("unxed/f4")
        self.assertEqual(api.call_args.kwargs.get("check"), False)

    def test_preserved_repo_never_cancels_and_does_not_ask_about_nightly(self):
        with mock.patch.object(train, "nightly_is_stale") as stale:
            self.assertFalse(train.should_cancel_main_run("unxed/vtui"))
        stale.assert_not_called()

    def test_f4_cancels_only_while_nightly_is_fresh(self):
        with mock.patch.object(train, "nightly_is_stale", return_value=True):
            self.assertFalse(train.should_cancel_main_run("unxed/f4"))
        with mock.patch.object(train, "nightly_is_stale", return_value=False):
            self.assertTrue(train.should_cancel_main_run("unxed/f4"))

    def test_other_project_cancels_as_before(self):
        self.assertTrue(train.should_cancel_main_run("unxed/tar"))


if __name__ == "__main__":
    unittest.main()
