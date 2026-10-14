import contextlib
import io
import subprocess
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


class StuckTest(unittest.TestCase):
    @staticmethod
    def commit(sha, message, when):
        return {"sha": sha, "parents": [{}], "commit": {
            "message": message,
            "committer": {"date": when.isoformat().replace("+00:00", "Z")},
        }}

    def check_stuck(self, commits):
        with mock.patch.object(train, "api", side_effect=[
                {"commit": {"sha": "main"}}, {"commit": {"sha": "staging"}}]), \
                mock.patch.object(train, "green_train_covering", return_value=None), \
                mock.patch.object(train, "compare", return_value={"commits": commits}), \
                contextlib.redirect_stdout(io.StringIO()) as output:
            result = train.stuck("o/r")
        return result, output.getvalue()

    def test_old_commit_reverted_on_staging_does_not_trigger_stuck(self):
        now = datetime.now(timezone.utc)
        commits = [
            self.commit("a" * 40, "old work", now - timedelta(hours=7)),
            self.commit("b" * 40, 'Revert "old work"\n\nThis reverts commit ' + "a" * 40 + ".",
                        now - timedelta(minutes=10)),
        ]
        result, output = self.check_stuck(commits)
        self.assertEqual(result, 0)
        self.assertIn("1 коммит(ов) ждут main", output)
        self.assertNotIn("ИНЦИДЕНТ ПРОЦЕССА", output)

    def test_new_ordinary_commit_is_still_counted_for_stuck(self):
        now = datetime.now(timezone.utc)
        commits = [self.commit("c" * 40, "new work", now - timedelta(minutes=10))]
        result, output = self.check_stuck(commits)
        self.assertEqual(result, 0)
        self.assertIn("1 коммит(ов) ждут main", output)


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


class HealRerunTest(unittest.TestCase):
    def test_red_staging_rerun_uses_checked_rest_endpoint(self):
        last = {"html_url": "https://github.com/o/r/actions/runs/42",
                "head_sha": "abcdef123", "id": 42, "run_attempt": 1}
        with mock.patch.object(train, "staging_health", return_value=("red", {"last": last})), \
                mock.patch.object(train, "api") as api:
            self.assertEqual(train.heal("o/r"), 0)
        api.assert_called_once_with("repos/o/r/actions/runs/42/rerun-failed-jobs", "-X", "POST")


class DispatchFormatWarnTest(unittest.TestCase):
    """14-10-2026: 5b329822 превратил захваты dn в строки формата CI.md; dispatch-lint упал один раз,
    следующие пуши зелёные (гейт видит только добавленные строки) — health/tick-all должны это видеть."""
    CI_LINE = ("14-10-2026 06:26:30 Лунобот-1 (node 801452e4fd3b9a26f8e6f02c; LNX), тикет "
               "https://github.com/unxed/dn/issues/36, PR [#45](https://github.com/unxed/dn/pull/45), "
               "коммит `0fe1a68`\n")
    STALE_OK = ("01-01-2026 00:00:00 Я Лунобот-1 (node 801452e4fd3b9a26f8e6f02c; LNX) взял "
                "https://github.com/unxed/dn/issues/7 [land]\n")

    def run_warn(self, files):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as root:
            for name, text in files.items():
                os.makedirs(os.path.join(root, "projects", name))
                with open(os.path.join(root, "projects", name, "DISPATCH.md"), "w", encoding="utf-8") as f:
                    f.write(text)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                train.dispatch_format_warn(root)
            return out.getvalue()

    def test_ci_md_line_in_dispatch_warns(self):
        out = self.run_warn({"dn": "# DISPATCH\n\n" + self.CI_LINE, "f4": "# DISPATCH\n"})
        self.assertIn("ПРЕДУПРЕЖДЕНИЕ: DISPATCH.md dn: формат", out)
        self.assertNotIn("DISPATCH.md f4", out)

    def test_stale_but_well_formed_claim_is_silent(self):
        self.assertEqual(self.run_warn({"dn": "# DISPATCH\n\n" + self.STALE_OK}), "")

    def test_health_warns_without_changing_rc(self):
        with mock.patch.object(train, "staging_health", return_value=("green", {"last": None})), \
                mock.patch.object(train, "stuck", return_value=0), \
                mock.patch.object(train, "main_ci", return_value=0), \
                mock.patch.object(train, "transit_warn"), \
                mock.patch.object(train, "dispatch_format_warn") as warn, \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(train.health("o/r"), 0)
        warn.assert_called_once_with()


class CancelRunTest(unittest.TestCase):
    def test_cancel_uses_rest_endpoint(self):
        with mock.patch.object(train, "api") as api:
            train.cancel_run("o/r", 42)
        api.assert_called_once_with("repos/o/r/actions/runs/42/cancel", "-X", "POST")


class BisectDispatchTest(unittest.TestCase):
    COMMITS = [{"sha": "a" * 40}, {"sha": "b" * 40}]
    PR = {"number": 7, "base": {"sha": "c" * 40}}

    def test_workflow_cli_failure_falls_back_to_checked_rest_dispatch(self):
        def run(*args, **kwargs):
            if args[0:3] == ("gh", "workflow", "run"):
                return subprocess.CompletedProcess(args, 1, "", "GraphQL unavailable")
            return subprocess.CompletedProcess(args, 0, "", "")

        with mock.patch.object(train, "train_commits", return_value=self.COMMITS), \
                mock.patch.object(train, "api"), \
                mock.patch.object(train, "sandbox_cmd", return_value="go test ./..."), \
                mock.patch.object(train, "run", side_effect=run) as mocked_run:
            self.assertIsNone(train.bisect("o/r", self.PR, "ubuntu-latest", "go test ./...",
                                           good=-1, bad=0))

        fallbacks = [call.args for call in mocked_run.call_args_list
                     if call.args[0:3] == ("gh", "api", "-X")]
        self.assertEqual(len(fallbacks), 2)
        self.assertEqual(fallbacks[0], (
            "gh", "api", "-X", "POST", "repos/o/r/actions/workflows/sandbox.yml/dispatches",
            "-f", "ref=bisect/7/base-ccccccccc", "-f", "inputs[os]=ubuntu-latest",
            "-f", "inputs[command]=go test ./..."))

    def test_failed_rest_dispatch_is_reported(self):
        def run(*args, **kwargs):
            return subprocess.CompletedProcess(args, 1, "", "HTTP 403")

        with mock.patch.object(train, "train_commits", return_value=self.COMMITS), \
                mock.patch.object(train, "api"), \
                mock.patch.object(train, "sandbox_cmd", return_value="go test ./..."), \
                mock.patch.object(train, "run", side_effect=run):
            with self.assertRaisesRegex(SystemExit, "не удалось запустить sandbox.yml.*HTTP 403"):
                train.bisect("o/r", self.PR, "ubuntu-latest", "go test ./...",
                             good=-1, bad=0)


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

    def run_tick(self, tip, total, ahead=1, rc=0):
        dispatched = []

        def fake_api(path, *args, check=True):
            if path.endswith(f"branches/{train.STAGING}"):
                return tip
            if "/compare/" in path:
                return {"ahead_by": ahead}
            if "quick.yml/runs" in path:
                return {"total_count": total}
            return {}

        def fake_run(*cmd, check=True, cwd=None):
            dispatched.append(cmd)
            return subprocess.CompletedProcess(cmd, rc, "", "HTTP 422: Workflow does not have 'workflow_dispatch' trigger" if rc else "")

        out = io.StringIO()
        with mock.patch.object(train, "api", fake_api), mock.patch.object(train, "run", fake_run), \
                contextlib.redirect_stdout(out):
            train.ensure_quick_on_tip("o/r")
        self.out = out.getvalue()
        return [c for c in dispatched if any("dispatches" in a for a in c)]

    def test_old_tip_without_runs_gets_quick_dispatched(self):
        dispatched = self.run_tick(self.tip(30), 0)
        self.assertEqual(len(dispatched), 1)
        self.assertIn(f"ref={train.STAGING}", dispatched[0])
        self.assertIn("запустил quick вручную", self.out)

    def test_fresh_tip_is_left_to_the_push_trigger(self):
        self.assertEqual(self.run_tick(self.tip(2), 0), [])

    def test_tip_with_a_run_is_left_alone(self):
        self.assertEqual(self.run_tick(self.tip(60), 1), [])

    def test_staging_with_nothing_beyond_main_needs_no_quick(self):
        self.assertEqual(self.run_tick(self.tip(600), 0, ahead=0), [])
        self.assertEqual(self.out, "")

    def test_a_refused_dispatch_is_not_reported_as_started(self):
        self.assertEqual(len(self.run_tick(self.tip(30), 0, rc=1)), 1)
        self.assertNotIn("запустил quick вручную", self.out)
        self.assertIn("НЕ вышло", self.out)
        self.assertIn("workflow_dispatch", self.out)


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


class MainCancelledRunTest(unittest.TestCase):
    def _fake_api(self, attempt, calls):
        def api(path, *args, check=True):
            calls.append((path, args))
            if path.endswith("/branches/main"):
                return {"commit": {"sha": "abc123def"}}
            if "actions/runs?" in path:
                return {"workflow_runs": [{"id": 7, "name": "CI", "status": "completed",
                                           "conclusion": "cancelled", "run_attempt": attempt,
                                           "created_at": "2026-10-09T19:29:03Z",
                                           "html_url": "https://example/runs/7"}]}
            return {}
        return api

    def test_cancelled_main_run_is_rerun_once(self):
        calls = []
        with mock.patch.object(train, "api", side_effect=self._fake_api(1, calls)):
            self.assertEqual(train.main_ci("o/r"), 0)
        self.assertIn(("repos/o/r/actions/runs/7/rerun", ("-X", "POST")), calls)

    def test_cancelled_again_is_not_rerun_forever(self):
        calls = []
        with mock.patch.object(train, "api", side_effect=self._fake_api(2, calls)):
            train.main_ci("o/r")
        self.assertFalse(any(p.endswith("/rerun") for p, _ in calls))



class RollupRestRerunTest(unittest.TestCase):
    def test_failed_check_from_rest_can_be_rerun(self):
        def api(path, *args, check=True):
            if path.endswith("/pulls/5"):
                return {"head": {"sha": "abc"}}
            if "check-runs" in path:
                return {"check_runs": [{"name": "Race (shard 3)", "status": "completed",
                                        "conclusion": "failure",
                                        "details_url": "https://github.com/o/r/actions/runs/42/job/7"}]}
            if path.endswith("/status"):
                return {"statuses": []}
            return {}
        with mock.patch.object(train, "api", side_effect=api):
            checks = train.rollup_rest("o/r", 5)
        posted = []
        with mock.patch.object(train, "api", side_effect=lambda p, *a, check=True: posted.append((p, a, check))):
            train.rerun(checks)
        self.assertEqual(posted, [("repos/o/r/actions/runs/42/rerun-failed-jobs", ("-X", "POST"), True)])

    def test_failed_rerun_request_is_not_silently_ignored(self):
        checks = [{"detailsUrl": "https://github.com/o/r/actions/runs/42/job/7"}]
        with mock.patch.object(train, "api", side_effect=SystemExit("request failed")) as api:
            with self.assertRaisesRegex(SystemExit, "request failed"):
                train.rerun(checks)
        api.assert_called_once_with("repos/o/r/actions/runs/42/rerun-failed-jobs", "-X", "POST")


if __name__ == "__main__":
    unittest.main()


class TriedSinceTest(unittest.TestCase):
    """Тикет из нескольких частей: «Пробуйте!» после его последнего коммита в main снимает предупреждение."""

    commits = [{"commit": {"message": "feat: x\n\nTouch: unxed/f4#7\n", "committer": {"date": "2026-10-10T01:00:00Z"}}}]

    def check(self, comments):
        with mock.patch.object(train, "api", return_value=comments):
            return train.tried_since("unxed/f4", 7, self.commits)

    def test_try_after_the_commit_counts(self):
        self.assertTrue(self.check([{"body": "Пробуйте! всё", "created_at": "2026-10-10T02:00:00Z"}]))

    def test_lowercase_try_after_the_commit_counts(self):
        self.assertTrue(self.check([{"body": "Привет, попробуйте! изменение", "created_at": "2026-10-10T02:00:00Z"}]))

    def test_lowercase_try_from_real_ticket_counts(self):
        # unxed/f4#1898, 13-10-2026: «@nz256, пробуйте! …» — ложное «нет «Пробуйте!»» в tick-all.
        self.assertTrue(self.check([{"body": "@nz256, пробуйте! Исправление в main", "created_at": "2026-10-10T02:00:00Z"}]))
        self.assertTrue(self.check([{"body": "ПРОБУЙТЕ! всё", "created_at": "2026-10-10T02:00:00Z"}]))

    def test_try_without_exclamation_does_not_count(self):
        self.assertFalse(self.check([{"body": "пробуйте позже", "created_at": "2026-10-10T02:00:00Z"}]))

    def test_other_comments_do_not(self):
        self.assertFalse(self.check([{"body": "спасибо", "created_at": "2026-10-10T02:00:00Z"}]))
        self.assertFalse(self.check(None))

    def test_ticket_without_commits_is_not_tried(self):
        with mock.patch.object(train, "api", return_value=[{"body": "Пробуйте!", "created_at": "2026-10-10T02:00:00Z"}]):
            self.assertFalse(train.tried_since("unxed/f4", 8, self.commits))


class CheckSectionTest(unittest.TestCase):
    TOUCH = "\n\nTouch: unxed/f4#912\n"

    def test_human_text_on_next_line_passes(self):
        body = "fix\n\nПроверить:\nОткройте меню дисков: Bookmarks теперь под Tools." + self.TOUCH
        self.assertIsNone(train.check_section_problem(body))

    def test_human_text_on_same_line_passes(self):
        # 57 из 300 коммитов main f4 пишут текст в той же строке — это нормальный текст.
        body = "fix\n\nПроверить: Windows: Alt+F6 → «Жёсткая ссылка» — ссылка рядом." + self.TOUCH
        self.assertIsNone(train.check_section_problem(body))

    def test_command_on_same_line_is_refused(self):
        body = "fix\n\nПроверить: go test ./vfs/ -run TestSudoClient — зелёный." + self.TOUCH
        self.assertIn("команда", train.check_section_problem(body))

    def test_empty_section_before_trailers_is_not_text(self):
        body = ("fix\n\nTouch: unxed/vtui#5\n\nПроверить:\n\n"
                "Lunobot-Instance: Лунобот-1 (node a; LNX)\nCo-Authored-By: X <x@y>\n")
        self.assertEqual(train.check_text(body), "")
        self.assertIn("нет текста", train.check_section_problem(body))

    def test_go_test_command_is_refused(self):
        body = "fix\n\nПроверить:\ngo test -run TestX ./internal/panel/" + self.TOUCH
        self.assertIn("команда", train.check_section_problem(body))

    def test_touch_without_section_is_refused(self):
        self.assertIn("нет текста", train.check_section_problem("fix" + self.TOUCH))

    def test_custom_task_may_skip_section(self):
        self.assertIsNone(train.check_section_problem("ci: fix\n\nLunobot-Task: ci-fix\n"))

    def test_both_1889_commits_would_have_been_refused(self):
        body = ("panel: x\n\nПроблема: y\n\nTouch: unxed/f4#1148\n\n"
                "Проверить: go test -run 'TestA|TestB' ./internal/panel/\n\n"
                "Lunobot-Instance: Лунобот-1 (node a; LNX)\n")
        self.assertIsNotNone(train.check_section_problem(body))

    def test_text_starting_with_code_span_passes(self):
        body = "fix\n\nПроверить:\n`highlight.ini` теперь сохраняется." + self.TOUCH
        self.assertIsNone(train.check_section_problem(body))


class TicketsCheckTextTest(unittest.TestCase):
    """tick: текст «Проверить:» из коммитов поезда для «Пробуйте!»."""

    @staticmethod
    def commits(*messages):
        return [{"commit": {"message": m}, "parents": [{}]} for m in messages]

    def test_text_on_same_line_and_next_line_are_both_read(self):
        got = train.tickets("unxed/f4", self.commits(
            "a\n\nTouch: #1\n\nПроверить: откройте CSV, нажмите Alt+S.\n\nLunobot-Instance: x\n",
            "b\n\nTouch: #2\n\nПроверить:\nОткройте меню дисков.\nВторая строка.\n\nLunobot-Instance: x\n"))
        self.assertEqual(got, {"unxed/f4#1": ["откройте CSV, нажмите Alt+S."],
                               "unxed/f4#2": ["Откройте меню дисков.\nВторая строка."]})

    def test_commit_reverted_in_the_same_train_is_not_announced(self):
        commits = [
            {"sha": "aaa1111", "parents": [{}], "commit": {"message":
             "fix\n\nTouch: #912\n\nПроверить: откройте highlight.ini.\n"}},
            {"sha": "bbb2222", "parents": [{}], "commit": {"message":
             "viewer\n\nTouch: #1898\n\nПроверить: нажмите Shift+F7.\n"}},
            {"sha": "ccc3333", "parents": [{}], "commit": {"message":
             'Revert "fix"\n\nThis reverts commit aaa1111.\n\nStaging-Revert: u\n'}},
        ]
        self.assertEqual(train.tickets("unxed/f4", commits),
                         {"unxed/f4#1898": ["нажмите Shift+F7."]})
        self.assertEqual(list(train.summaries("unxed/f4", commits)), ["unxed/f4#1898"])

    def test_revert_of_a_commit_already_in_main_stays(self):
        commits = [{"sha": "ccc3333", "parents": [{}], "commit": {"message":
                    'Revert "x"\n\nThis reverts commit 9999999.\n\nTouch: #7\n'}}]
        self.assertEqual(train.tickets("unxed/f4", commits), {"unxed/f4#7": []})

    def test_command_and_trailers_never_reach_the_user(self):
        got = train.tickets("unxed/f4", self.commits(
            "a\n\nTouch: #1\n\nПроверить: go test -run TestA ./internal/panel/\n\nLunobot-Instance: x\n",
            "b\n\nLunobot-Task: ci\n\nПроверить:\n\nLunobot-Instance: x\nCo-Authored-By: y\n"))
        self.assertEqual(got, {"unxed/f4#1": [], "ci": []})


class TickAllTest(unittest.TestCase):
    def test_failure_of_one_project_does_not_skip_the_rest(self):
        calls = []

        def fake_tick(repo, sign):
            calls.append(repo)
            if repo == "o/a":
                raise SystemExit("gh api: TLS handshake timeout")
            return 0

        with mock.patch.object(train, "staged_repos", return_value=["o/a", "o/b"]), \
                mock.patch.object(train, "tick", side_effect=fake_tick), \
                mock.patch.object(train, "dispatch_format_warn"), \
                contextlib.redirect_stdout(io.StringIO()) as out:
            rc = train.tick_all("sig")
        self.assertEqual(calls, ["o/a", "o/b"])
        self.assertEqual(rc, 1)
        self.assertIn("ОШИБКА tick o/a", out.getvalue())
