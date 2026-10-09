import unittest
from datetime import datetime, timedelta, timezone
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


class PickGreenTest(unittest.TestCase):
    """Поезд режется только от зелёного коммита, который уже содержит main."""

    def pick(self, runs, behind):
        def compare(repo, base, head):
            if base == "main":
                return {"ahead_by": 3, "behind_by": behind[head]}
            return {"status": "ahead"}
        with mock.patch.object(train, "compare", side_effect=compare):
            return train.pick_green("o/r", "main", "tip", runs)

    def test_green_commit_behind_main_is_skipped(self):
        runs = [{"conclusion": "success", "head_sha": "old"}]
        self.assertIsNone(self.pick(runs, {"old": 5}))

    def test_green_commit_with_main_is_taken(self):
        runs = [{"conclusion": "failure", "head_sha": "red"},
                {"conclusion": "success", "head_sha": "new"},
                {"conclusion": "success", "head_sha": "old"}]
        self.assertEqual(self.pick(runs, {"red": 0, "new": 0, "old": 5})["head_sha"], "new")

    def test_newer_green_behind_main_does_not_hide_older_one_with_main(self):
        runs = [{"conclusion": "success", "head_sha": "a"}, {"conclusion": "success", "head_sha": "b"}]
        self.assertEqual(self.pick(runs, {"a": 2, "b": 0})["head_sha"], "b")


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


class TrainStepCancellationTest(unittest.TestCase):
    def test_cancelled_checks_are_restarted_while_other_checks_are_queued(self):
        pr = {"number": 197, "head": {"sha": "head"}}
        cancelled = [{"conclusion": "CANCELLED",
                      "detailsUrl": "https://github.com/o/r/actions/runs/42"}]
        pending = [{"status": "QUEUED"}]
        with mock.patch.object(train, "train_pr", return_value=pr), \
                mock.patch.object(train, "rollup", return_value=(pending + cancelled,
                                                                    pending, [], cancelled)), \
                mock.patch.object(train, "rerun") as rerun:
            self.assertEqual(train.train_step("o/r", "sign"), 0)
        rerun.assert_called_once_with(cancelled)


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


    def test_naive_timestamp_is_taken_as_utc(self):
        naive_old = {"published_at": "2020-01-01T00:00:00"}
        naive_fresh = {"published_at": train.datetime.now(train.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")}
        with mock.patch.object(train, "api", return_value=naive_old):
            self.assertTrue(train.nightly_is_stale("unxed/f4"))
        with mock.patch.object(train, "api", return_value=naive_fresh):
            self.assertFalse(train.nightly_is_stale("unxed/f4"))


class MainPushRunsTest(unittest.TestCase):
    def test_only_unfinished_push_runs_are_returned(self):
        resp = {"workflow_runs": [
            {"id": 1, "event": "push", "status": "in_progress"},
            {"id": 2, "event": "push", "status": "completed"},
            {"id": 3, "event": "pull_request", "status": "queued"},
        ]}
        with mock.patch.object(train, "api", return_value=resp):
            self.assertEqual([r["id"] for r in train.main_push_runs_in_progress("o/r", "abc")], [1])

    def test_gh_failure_and_broken_answers_give_nothing_to_cancel(self):
        for side in (SystemExit("gh api: 502"), RuntimeError("boom")):
            with mock.patch.object(train, "api", side_effect=side):
                self.assertEqual(train.main_push_runs_in_progress("o/r", "abc"), [])
        for answer in (None, {"message": "Not Found"}, []):
            with mock.patch.object(train, "api", return_value=answer):
                self.assertEqual(train.main_push_runs_in_progress("o/r", "abc"), [])

    def test_api_is_called_without_check(self):
        with mock.patch.object(train, "api", return_value={"workflow_runs": []}) as api:
            train.main_push_runs_in_progress("o/r", "abc")
        self.assertEqual(api.call_args.kwargs.get("check"), False)

class EnsureQuickOnTipTest(unittest.TestCase):
    def tip(self, minutes):
        when = (datetime.now(timezone.utc) - timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")
        return {"commit": {"sha": "a" * 40, "commit": {"committer": {"date": when}}}}

    def run_tick(self, tip, total):
        calls = []

        def fake_api(path, *args, check=True):
            calls.append((path, args))
            if path.endswith(f"branches/{train.STAGING}"):
                return tip
            if "quick.yml/runs" in path:
                return {"total_count": total}
            return {}

        with mock.patch.object(train, "api", fake_api):
            train.ensure_quick_on_tip("o/r")
        return [c for c in calls if "dispatches" in c[0]]

    def test_old_tip_without_runs_gets_quick_dispatched(self):
        dispatched = self.run_tick(self.tip(30), 0)
        self.assertEqual(len(dispatched), 1)
        self.assertIn(f"ref={train.STAGING}", dispatched[0][1])

    def test_fresh_tip_is_left_to_the_push_trigger(self):
        self.assertEqual(self.run_tick(self.tip(2), 0), [])

    def test_tip_with_a_run_is_left_alone(self):
        self.assertEqual(self.run_tick(self.tip(60), 1), [])


class SummariesTest(unittest.TestCase):
    """Тело PR поезда: под номером тикета очень короткая сводка проблемы и исправления."""

    @staticmethod
    def commit(message, parents=1):
        return {"commit": {"message": message}, "parents": [{}] * parents}

    def test_problem_and_fix_sections_are_used(self):
        msg = ("fix(menu): long subject line that must not be shown\n\nbody text\n\n"
               "Проблема: курсор тормозит в большой папке\n"
               "Исправление: меню опрашивается не на каждый кадр\n\n"
               "Touch: unxed/f4#1832\n\nПроверить:\nпройдитесь по папке\n")
        got = train.summaries("unxed/f4", [self.commit(msg)])
        self.assertEqual(got, {"unxed/f4#1832": {
            "problem": ["курсор тормозит в большой папке"],
            "fix": ["меню опрашивается не на каждый кадр"]}})

    def test_without_sections_the_subject_is_the_fix(self):
        got = train.summaries("unxed/f4", [self.commit("fix(x): short subject\n\nTouch: #5\n")])
        self.assertEqual(got["unxed/f4#5"], {"problem": [], "fix": ["fix(x): short subject"]})

    def test_repeats_are_dropped_and_long_text_is_cut(self):
        long_fix = "а" * 500
        msgs = [self.commit(f"s\n\nПроблема: одна\nИсправление: {long_fix}\n\nTouch: #7\n")] * 2
        got = train.summaries("unxed/f4", msgs)["unxed/f4#7"]
        self.assertEqual(got["problem"], ["одна"])
        self.assertEqual(len(got["fix"]), 1)
        self.assertLessEqual(len(got["fix"][0]), train.SUMMARY_LEN)

    def test_merge_commits_and_commits_without_a_trailer_are_skipped(self):
        got = train.summaries("unxed/f4", [self.commit("Merge\n\nTouch: #1\n", parents=2),
                                           self.commit("no trailer here\n")])
        self.assertEqual(got, {})


if __name__ == "__main__":
    unittest.main()
