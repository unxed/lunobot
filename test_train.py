import contextlib
import io
import subprocess
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

import train


def _proc(code=0, out="", err=""):
    return subprocess.CompletedProcess([], code, out, err)


class ApiRetryTest(unittest.TestCase):
    """Обрыв связи посреди ответа не должен ронять круг: 15-10-2026 `tick-all` остановил vtui на
    `unexpected end of JSON input` от `gh api compare`, второй запуск прошёл."""

    def test_transient_read_error_is_retried(self):
        runs = [_proc(1, "", "unexpected end of JSON input"), _proc(0, '{"a": 1}')]
        with mock.patch.object(train, "run", side_effect=runs) as run, mock.patch.object(train.time, "sleep"):
            self.assertEqual(train.api("repos/o/r/compare/a...b"), {"a": 1})
        self.assertEqual(run.call_count, 2)

    def test_bare_go_client_eof_is_retried(self):
        eof = _proc(1, "", 'Get "https://api.github.com/repos/o/r/compare/a...b": EOF')
        with mock.patch.object(train, "run", side_effect=[eof, _proc(0, '{"a": 1}')]) as run, \
                mock.patch.object(train.time, "sleep"):
            self.assertEqual(train.api("repos/o/r/compare/a...b"), {"a": 1})
        self.assertEqual(run.call_count, 2)

    def test_gateway_5xx_is_retried(self):
        timeout = _proc(1, "", "gh: We couldn't respond to your request in time. Sorry about that. (HTTP 504)")
        with mock.patch.object(train, "run", side_effect=[timeout, _proc(0, '{"a": 1}')]) as run, \
                mock.patch.object(train.time, "sleep"):
            self.assertEqual(train.api("repos/o/r/actions/workflows/quick.yml/runs?per_page=100"), {"a": 1})
        self.assertEqual(run.call_count, 2)

    def test_gives_up_after_the_limit_and_reports_the_error(self):
        err = _proc(1, "", "stream error: INTERNAL_ERROR")
        with mock.patch.object(train, "run", return_value=err) as run, \
                mock.patch.object(train.time, "sleep") as sleep:
            with self.assertRaises(SystemExit) as cm:
                train.api("repos/o/r/compare/a...b")
        self.assertEqual(run.call_count, train.API_RETRIES)
        # Паузы только между попытками (2 и 4 с), после последней не спим.
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [2, 4])
        self.assertIn("stream error", str(cm.exception))

    def test_other_errors_are_not_retried(self):
        with mock.patch.object(train, "run", return_value=_proc(1, "", "HTTP 404: Not Found")) as run:
            with self.assertRaises(SystemExit):
                train.api("repos/o/r/git/ref/heads/x")
        self.assertEqual(run.call_count, 1)

    def test_check_false_returns_the_body_without_exit(self):
        with mock.patch.object(train, "run", return_value=_proc(1, '{"message": "Not Found"}', "HTTP 404")):
            self.assertEqual(train.api("repos/o/r/x", check=False), {"message": "Not Found"})

    def test_writes_are_never_repeated(self):
        err = _proc(1, "", "unexpected end of JSON input")
        for args in (("-X", "POST"), ("-X", "PUT"), ("-f", "ref=refs/heads/x")):
            with mock.patch.object(train, "run", return_value=err) as run:
                with self.assertRaises(SystemExit):
                    train.api("repos/o/r/git/refs", *args)
            self.assertEqual(run.call_count, 1, args)

    def test_query_fields_keep_the_request_a_read(self):
        self.assertTrue(train.api_is_read(["-X", "GET", "-f", "branch=lunobot/staging"]))


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


class CoveredTest(unittest.TestCase):
    def test_verdict_names_the_requested_commit_and_covering_run(self):
        sha = "0123456789abcdef"
        run = {
            "status": "completed",
            "conclusion": "failure",
            "created_at": "2026-10-15T00:00:00Z",
            "head_sha": "fedcba9876543210",
            "html_url": "https://github.com/o/r/actions/runs/1",
        }
        output = io.StringIO()
        with mock.patch.object(train, "api", side_effect=[
            {"workflow_runs": [run]}, {"status": "ahead"},
        ]), \
                contextlib.redirect_stdout(output):
            self.assertEqual(train.covered("o/r", sha), 1)
        self.assertIn("КРАСНЫЙ для 012345678: https://github.com/o/r/actions/runs/1", output.getvalue())
        self.assertIn("прогон на fedcba9", output.getvalue())


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


class VendorsyncToRevertTest(unittest.TestCase):
    """heal откатывает vendorhash-autosync вместе с виновником, правившим go.mod (поезд #1968)."""

    @staticmethod
    def commit(sha, msg):
        return {"sha": sha, "commit": {"message": msg}, "parents": [{}]}

    VENDOR = VendorHashTest.VENDOR

    def test_autosync_after_a_reverted_gomod_change_is_reverted_too(self):
        after = [self.commit("bump", "bump\n\nTouch: #1\n"), self.commit("v1", self.VENDOR),
                 self.commit("w", "work\n\nTouch: #2\n"), self.commit("v2", self.VENDOR)]
        self.assertEqual(train.vendorsync_to_revert(after, ["bump"], ["bump"]), ["v2", "v1"])

    def test_nothing_when_no_culprit_touched_gomod(self):
        after = [self.commit("w", "work\n\nTouch: #2\n"), self.commit("v1", self.VENDOR)]
        self.assertEqual(train.vendorsync_to_revert(after, ["w"], []), [])

    def test_nothing_when_a_kept_commit_also_changed_gomod(self):
        after = [self.commit("a", "a\n\nTouch: #1\n"), self.commit("b", "b\n\nTouch: #2\n"),
                 self.commit("v1", self.VENDOR)]
        self.assertEqual(train.vendorsync_to_revert(after, ["a"], ["a", "b"]), [])


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

    def check_stuck(self, commits, train_pr=None, rollup=None):
        with mock.patch.object(train, "api", side_effect=[
                {"commit": {"sha": "main"}}, {"commit": {"sha": "staging"}}]), \
                mock.patch.object(train, "green_train_covering", return_value=None), \
                mock.patch.object(train, "train_pr", return_value=train_pr), \
                mock.patch.object(train, "rollup", return_value=rollup or ([], [], [], [])), \
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

    def test_recent_train_in_flight_does_not_trigger_old_staging_incident(self):
        now = datetime.now(timezone.utc)
        commits = [self.commit("d" * 40, "old work", now - timedelta(hours=4))]
        pr = {"number": 12, "head": {"sha": "staging"},
              "created_at": (now - timedelta(minutes=15)).isoformat()}
        result, output = self.check_stuck(commits, pr, ([{"status": "IN_PROGRESS"}],
                                                         [{"status": "IN_PROGRESS"}], [], []))
        self.assertEqual(result, 0)
        self.assertIn("поезд #12 проверяется", output)
        self.assertNotIn("ИНЦИДЕНТ ПРОЦЕССА", output)

    def test_train_in_flight_over_two_hours_triggers_incident(self):
        now = datetime.now(timezone.utc)
        commits = [self.commit("e" * 40, "old work", now - timedelta(hours=4))]
        pr = {"number": 13, "head": {"sha": "staging"},
              "created_at": (now - timedelta(hours=3)).isoformat()}
        result, output = self.check_stuck(commits, pr, ([{"status": "IN_PROGRESS"}],
                                                         [{"status": "IN_PROGRESS"}], [], []))
        self.assertEqual(result, 1)
        self.assertIn("проверяется 3.0 ч", output)
        self.assertIn("ИНЦИДЕНТ ПРОЦЕССА", output)

    def test_failed_or_cancelled_train_still_triggers_incident(self):
        now = datetime.now(timezone.utc)
        commits = [self.commit("f" * 40, "old work", now - timedelta(hours=4))]
        pr = {"number": 14, "head": {"sha": "staging"},
              "created_at": (now - timedelta(minutes=5)).isoformat()}
        for rollup in (([{}], [{"status": "IN_PROGRESS"}], [{"conclusion": "FAILURE"}], []),
                       ([{}], [{"status": "IN_PROGRESS"}], [], [{"conclusion": "CANCELLED"}])):
            result, output = self.check_stuck(commits, pr, rollup)
            self.assertEqual(result, 1)
            self.assertIn("ИНЦИДЕНТ ПРОЦЕССА", output)

    def test_train_for_other_head_or_no_train_still_triggers_incident(self):
        now = datetime.now(timezone.utc)
        commits = [self.commit("9" * 40, "old work", now - timedelta(hours=4))]
        pr = {"number": 15, "head": {"sha": "older-staging"},
              "created_at": (now - timedelta(minutes=5)).isoformat()}
        pending = ([{"status": "IN_PROGRESS"}], [{"status": "IN_PROGRESS"}], [], [])
        for train_pr in (None, pr):
            result, output = self.check_stuck(commits, train_pr, pending)
            self.assertEqual(result, 1)
            self.assertIn("ИНЦИДЕНТ ПРОЦЕССА", output)


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


class RerunRaceTest(unittest.TestCase):
    def test_already_running_is_not_an_error(self):
        err = SystemExit("gh api repos/o/r/actions/runs/7/rerun-failed-jobs -X POST: "
                         "gh: This workflow is already running (HTTP 403)")
        with mock.patch.object(train, "api", side_effect=err) as api:
            train.rerun_failed_jobs("o/r", 7)
        api.assert_called_once_with("repos/o/r/actions/runs/7/rerun-failed-jobs", "-X", "POST")

    def test_other_errors_still_stop_tick(self):
        with mock.patch.object(train, "api", side_effect=SystemExit("gh: Not Found (HTTP 404)")):
            with self.assertRaises(SystemExit):
                train.rerun_failed_jobs("o/r", 7)


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

    def test_completed_run_race_is_not_a_tick_failure(self):
        error = SystemExit("gh api: Cannot cancel a workflow run that is completed. (HTTP 409)")
        with mock.patch.object(train, "api", side_effect=error), \
                contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertIsNone(train.cancel_run("o/r", 42))
        self.assertIn("#42 уже завершён", output.getvalue())

    def test_unexpected_cancel_error_still_fails(self):
        error = SystemExit("gh api: Resource not accessible by integration (HTTP 403)")
        with mock.patch.object(train, "api", side_effect=error):
            with self.assertRaises(SystemExit):
                train.cancel_run("o/r", 42)


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


class NightlyTryNoteTest(unittest.TestCase):
    """nightly_try_note: the reminder for the one who posts «Пробуйте!» exists only for projects
    that ship builds through the floating nightly release (unxed/f4#1758, 17-10-2026)."""

    def test_project_with_nightly_gets_the_note_with_the_release_link(self):
        note = train.nightly_try_note("unxed/f4")
        self.assertIn("https://github.com/unxed/f4/releases/tag/nightly", note)
        self.assertIn("Пробуйте!", note)

    def test_project_without_nightly_gets_no_note(self):
        self.assertEqual(train.nightly_try_note("unxed/vtui"), "")


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

    def run_tick(self, tip, total, ahead=1, rc=0, files=None):
        dispatched = []

        def fake_api(path, *args, check=True):
            if path.endswith(f"branches/{train.STAGING}"):
                return tip
            if "/compare/" in path:
                return {"ahead_by": ahead} if files is None else {"ahead_by": ahead, "files": files}
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

    def test_error_body_instead_of_the_branch_is_skipped(self):
        # 14-10-2026: gh api вернул тело ошибки, и tick-all упал с KeyError: 'commit'.
        self.assertEqual(self.run_tick({"message": "API rate limit exceeded"}, 0), [])
        self.assertIn("не прочитана", self.out)

    def test_tip_with_a_run_is_left_alone(self):
        self.assertEqual(self.run_tick(self.tip(60), 1), [])

    def test_staging_with_nothing_beyond_main_needs_no_quick(self):
        self.assertEqual(self.run_tick(self.tip(600), 0, ahead=0), [])
        self.assertEqual(self.out, "")

    def test_empty_merge_of_main_needs_no_quick(self):
        # слияние main в staging без правок: ahead_by > 0, но diff пуст
        self.assertEqual(self.run_tick(self.tip(600), 0, ahead=1, files=[]), [])
        self.assertEqual(self.out, "")

    def test_ahead_with_changed_files_still_gets_quick(self):
        self.assertEqual(len(self.run_tick(self.tip(600), 0, ahead=1, files=[{"filename": "a.go"}])), 1)

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

    def _merge_api(self, calls, parent_trees=("T", "X"), parent_runs=None, merge_tree="T", parents=("p1", "p2")):
        base = self._fake_api(1, calls)
        parent_runs = parent_runs if parent_runs is not None else [
            {"name": "CI", "status": "completed", "conclusion": "success"},
            {"name": "quick", "status": "completed", "conclusion": "failure"}]

        def api(path, *args, check=True):
            if path == "repos/o/r/commits/abc123def":
                return {"commit": {"tree": {"sha": merge_tree}}, "parents": [{"sha": s} for s in parents]}
            if path == "repos/o/r/commits/p1":
                return {"commit": {"tree": {"sha": parent_trees[0]}}, "parents": []}
            if path == "repos/o/r/commits/p2":
                return {"commit": {"tree": {"sha": parent_trees[1]}}, "parents": []}
            if path.startswith("repos/o/r/actions/runs?head_sha=p"):
                calls.append((path, args))
                return {"workflow_runs": parent_runs}
            return base(path, *args, check=check)
        return api

    def _run_merge(self, **kw):
        calls = []
        with mock.patch.object(train, "api", side_effect=self._merge_api(calls, **kw)), \
                mock.patch("builtins.print") as pr:
            rc = train.main_ci("o/r")
        reran = any(p.endswith("/rerun") for p, _ in calls)
        return rc, reran, [str(c.args[0]) for c in pr.call_args_list]

    def test_cancelled_merge_commit_with_green_parent_tree_is_not_rerun(self):
        rc, reran, out = self._run_merge()
        self.assertEqual(rc, 0)
        self.assertFalse(reran)
        self.assertIn("main abc123def: прогон отменён, но дерево совпадает с зелёным p1 — повтор не нужен", out)

    def test_cancelled_merge_commit_second_parent_green(self):
        rc, reran, _ = self._run_merge(parent_trees=("X", "T"))
        self.assertEqual(rc, 0)
        self.assertFalse(reran)

    def test_cancelled_merge_commit_tree_differs_is_rerun(self):
        _, reran, _ = self._run_merge(merge_tree="OTHER")
        self.assertTrue(reran)

    def test_cancelled_merge_commit_parent_not_green_is_rerun(self):
        for runs in ([], [{"name": "CI", "status": "completed", "conclusion": "failure"}],
                     [{"name": "CI", "status": "in_progress", "conclusion": None}],
                     [{"name": "CI", "status": "completed", "conclusion": "success"},
                      {"name": "CI", "status": "completed", "conclusion": "cancelled"}],
                     [{"name": "CI", "status": "completed", "conclusion": "skipped"}],
                     [{"name": "quick", "status": "completed", "conclusion": "success"}]):
            with self.subTest(runs=runs):
                _, reran, _ = self._run_merge(parent_runs=runs)
                self.assertTrue(reran)

    def test_cancelled_non_merge_commit_is_rerun(self):
        _, reran, _ = self._run_merge(parents=("p1",))
        self.assertTrue(reran)

    def test_cancelled_merge_commit_api_error_is_rerun(self):
        calls = []
        merge_api = self._merge_api(calls)

        def broken(path, *args, check=True):
            if path.startswith("repos/o/r/commits/"):
                return {"message": "Server Error"}
            return merge_api(path, *args, check=check)
        with mock.patch.object(train, "api", side_effect=broken):
            self.assertEqual(train.main_ci("o/r"), 0)
        self.assertTrue(any(p.endswith("/rerun") for p, _ in calls))

    def test_cancelled_again_is_not_rerun_forever(self):
        calls = []
        with mock.patch.object(train, "api", side_effect=self._fake_api(2, calls)):
            train.main_ci("o/r")
        self.assertFalse(any(p.endswith("/rerun") for p, _ in calls))



class MainRedRunRerunTest(unittest.TestCase):
    def _fake_api(self, attempt, failed_jobs, calls):
        def api(path, *args, check=True):
            calls.append((path, args))
            if path.endswith("/branches/main"):
                return {"commit": {"sha": "abc123def"}}
            if "actions/runs?" in path:
                return {"workflow_runs": [{"id": 9, "name": "CI", "status": "completed",
                                           "conclusion": "failure", "run_attempt": attempt,
                                           "created_at": "2026-10-14T13:40:24Z",
                                           "html_url": "https://example/runs/9"}]}
            if path.endswith("/jobs?per_page=100"):
                return {"jobs": [{"name": f"job{i}", "conclusion": "failure"} for i in range(failed_jobs)]
                        + [{"name": "ok", "conclusion": "success"}]}
            return {}
        return api

    def test_single_failed_job_is_rerun_once(self):
        calls = []
        with mock.patch.object(train, "api", side_effect=self._fake_api(1, 1, calls)):
            self.assertEqual(train.main_ci("o/r"), 0)
        self.assertIn(("repos/o/r/actions/runs/9/rerun-failed-jobs", ("-X", "POST")), calls)

    def test_many_failed_jobs_stay_red(self):
        calls = []
        with mock.patch.object(train, "api", side_effect=self._fake_api(1, 5, calls)):
            self.assertEqual(train.main_ci("o/r"), 1)
        self.assertFalse(any(p.endswith("/rerun-failed-jobs") for p, _ in calls))

    def test_running_matrix_with_one_failed_job_waits(self):
        calls = []
        api = self._fake_api(1, 1, calls)

        def running(path, *args, check=True):
            out = api(path, *args, check=check)
            if out and "workflow_runs" in out:
                out["workflow_runs"][0].update(status="in_progress", conclusion=None)
            return out
        with mock.patch.object(train, "api", side_effect=running):
            self.assertEqual(train.main_ci("o/r"), 0)
        self.assertFalse(any(p.endswith("/rerun-failed-jobs") for p, _ in calls))

    def test_running_retry_with_failed_job_waits_for_retry_result(self):
        calls = []
        api = self._fake_api(2, 1, calls)

        def running(path, *args, check=True):
            out = api(path, *args, check=check)
            if out and "workflow_runs" in out:
                out["workflow_runs"][0].update(status="in_progress", conclusion=None)
            return out
        with mock.patch.object(train, "api", side_effect=running):
            self.assertEqual(train.main_ci("o/r"), 0)
        self.assertFalse(any(p.endswith("/rerun-failed-jobs") for p, _ in calls))

    def test_running_matrix_with_many_failed_jobs_is_red(self):
        calls = []
        api = self._fake_api(1, 5, calls)

        def running(path, *args, check=True):
            out = api(path, *args, check=check)
            if out and "workflow_runs" in out:
                out["workflow_runs"][0].update(status="in_progress", conclusion=None)
            return out
        with mock.patch.object(train, "api", side_effect=running):
            self.assertEqual(train.main_ci("o/r"), 1)

    def test_red_after_rerun_stays_red(self):
        calls = []
        with mock.patch.object(train, "api", side_effect=self._fake_api(2, 1, calls)):
            self.assertEqual(train.main_ci("o/r"), 1)
        self.assertFalse(any(p.endswith("/rerun-failed-jobs") for p, _ in calls))


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

    def test_runs_of_other_branches_on_the_train_commit_are_not_its_checks(self):
        def api(path, *args, check=True):
            if path.endswith("/pulls/5"):
                return {"head": {"sha": "abc", "ref": "lunobot/train/vtui/x"}}
            if "check-suites" in path:
                return {"check_suites": [{"id": 1, "head_branch": "lunobot/train/vtui/x"},
                                         {"id": 2, "head_branch": "tmp/19d3/golden-fix"}]}
            if "check-runs" in path:
                return {"check_runs": [
                    {"name": "Test (linux)", "status": "completed", "conclusion": "success",
                     "check_suite": {"id": 1}, "details_url": "u1"},
                    {"name": "Sandbox (ubuntu-latest)", "status": "completed", "conclusion": "failure",
                     "check_suite": {"id": 2}, "details_url": "u2"}]}
            if path.endswith("/status"):
                return {"statuses": []}
            return {}
        with mock.patch.object(train, "api", side_effect=api):
            checks = train.rollup_rest("o/r", 5)
        self.assertEqual([c["name"] for c in checks], ["Test (linux)"])

    def test_failed_rerun_request_is_not_silently_ignored(self):
        checks = [{"detailsUrl": "https://github.com/o/r/actions/runs/42/job/7"}]
        with mock.patch.object(train, "api", side_effect=SystemExit("request failed")) as api:
            with self.assertRaisesRegex(SystemExit, "request failed"):
                train.rerun(checks)
        api.assert_called_once_with("repos/o/r/actions/runs/42/rerun-failed-jobs", "-X", "POST")


class ApiErrorBodyTest(unittest.TestCase):
    """Тело ошибки GitHub вместо списка (лимит запросов) не роняет tried_since и transit_warn."""

    error = {"message": "API rate limit exceeded", "documentation_url": "https://docs.github.com"}

    def test_api_list_takes_only_a_list(self):
        with mock.patch.object(train, "api", return_value=self.error):
            self.assertEqual(train.api_list("repos/unxed/f4/commits"), [])
        with mock.patch.object(train, "api", return_value=None):
            self.assertEqual(train.api_list("repos/unxed/f4/commits"), [])
        with mock.patch.object(train, "api", return_value=[{"a": 1}]):
            self.assertEqual(train.api_list("repos/unxed/f4/commits"), [{"a": 1}])

    def test_tried_since_with_an_error_body_is_false(self):
        commits = [{"commit": {"message": "feat: x\n\nTouch: unxed/f4#7\n", "committer": {"date": "2026-10-10T01:00:00Z"}}}]
        with mock.patch.object(train, "api", return_value=self.error):
            self.assertFalse(train.tried_since("unxed/f4", 7, commits))


class MarkCheckingStagingPartTest(unittest.TestCase):
    """16-10-2026, поезд f4 #2006: часть 3 тикета #1998 влита, часть 4 (cba20e7f45, `Touch: #1998`)
    ещё в staging, а tick перевёл #1998 `в пути` → `проверяют`. Теперь такой тикет остаётся `в пути`."""

    REPO = "unxed/f4"
    SIGN = "Лунобот-1 (node 19d368003c6c048e43dbec70; LNX; Claude Sonnet 5.5; субагент)"
    TRIAGE = ("| тикет | приоритет | состояние | комментариев | updatedAt |\n"
              "| 1998 | 3 | в пути | 7 | 2026-10-16T01:00:00Z |\n"
              "| 2001 | 4 | в пути | 2 | 2026-10-16T01:00:00Z |\n")

    def setUp(self):
        import os
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        origin = os.path.join(self.tmp.name, "origin.git")
        self.clone = os.path.join(self.tmp.name, "acc")
        sh = lambda *a, cwd=None: subprocess.run(a, cwd=cwd, check=True, capture_output=True)
        sh("git", "init", "-q", "--bare", "-b", "main", origin)
        sh("git", "clone", "-q", origin, self.clone)
        self.path = os.path.join(self.clone, "TRIAGE.md")
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(self.TRIAGE)
        for a in (("add", "TRIAGE.md"),
                  ("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "init"),
                  ("push", "-q", "origin", "HEAD:main")):
            sh("git", *a, cwd=self.clone)
        for patch in (mock.patch.object(train, "ACCOUNTING", self.clone),
                      mock.patch.object(train, "triage_path", lambda repo: self.path)):
            patch.start()
            self.addCleanup(patch.stop)

    @staticmethod
    def commit(msg):
        return {"commit": {"message": msg}, "parents": [{}]}

    def mark(self, compare_resp, nums=(1998, 2001), branch_resp=None):
        def fake_api(path, *a, **kw):
            self.assertIs(kw.get("check"), False)  # ошибка API не должна ронять tick
            return compare_resp if "/compare/" in path else branch_resp
        out = io.StringIO()
        with mock.patch.object(train, "api", side_effect=fake_api), contextlib.redirect_stdout(out):
            train.mark_checking(self.REPO, set(nums), self.SIGN, "abc123")
        with open(self.path, encoding="utf-8") as f:
            return out.getvalue(), f.read()

    def test_ticket_with_a_part_in_staging_stays_in_transit(self):
        out, text = self.mark({"commits": [self.commit("fix: part 4\n\nTouch: #1998\n")]})
        self.assertIn("TRIAGE: остаются `в пути` (часть ещё в staging): #1998", out)
        self.assertIn("| 1998 | 3 | в пути |", text)
        self.assertIn("| 2001 | 4 | проверяют |", text)  # остальные тикеты поезда — как раньше
        self.assertIn("проверяют для #2001", out)

    def test_foreign_repo_touch_in_staging_does_not_hold(self):
        _, text = self.mark({"commits": [self.commit("x\n\nTouch: unxed/vtui#1998\n")]})
        self.assertIn("| 1998 | 3 | проверяют |", text)

    def test_all_held_makes_no_commit(self):
        before = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.clone, capture_output=True, text=True).stdout
        out, text = self.mark({"commits": [self.commit("a\n\nTouch: #1998\n"),
                                           self.commit("b\n\nTouch: #2001\n")]})
        self.assertIn("#1998, #2001", out)
        self.assertEqual(text, self.TRIAGE)
        after = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.clone, capture_output=True, text=True).stdout
        self.assertEqual(before, after)

    def test_triage_read_closes_file(self):
        import gc
        import warnings

        with warnings.catch_warnings(record=True) as seen:
            warnings.simplefilter("always", ResourceWarning)
            self.mark({"commits": []})
            gc.collect()

        self.assertFalse([warning for warning in seen
                          if issubclass(warning.category, ResourceWarning)])

    def test_empty_staging_marks_all_checking(self):
        out, text = self.mark({"commits": []})
        self.assertNotIn("остаются", out)
        self.assertNotIn("в пути |", text)

    def test_no_staging_branch_behaves_as_before_without_warning(self):
        for msg in ("Not Found", "Branch not found"):  # второй текст — реальный ответ GitHub (16-10-2026)
            with self.subTest(msg=msg):
                self.setUp()
                out, text = self.mark({"message": "Not Found"}, branch_resp={"message": msg})
                self.assertNotIn("ПРЕДУПРЕЖДЕНИЕ", out)
                self.assertNotIn("в пути |", text)

    def test_api_error_warns_and_marks_checking(self):
        for resp in ({"message": "API rate limit exceeded"}, None):
            with self.subTest(resp=resp):
                self.setUp()  # свежий клон для каждого прогона
                out, text = self.mark(resp, branch_resp=resp)
                self.assertIn("ПРЕДУПРЕЖДЕНИЕ", out)
                self.assertIn("| 1998 | 3 | проверяют |", text)
                self.assertIn("| 2001 | 4 | проверяют |", text)

    def test_train_step_passes_the_merged_head(self):
        with mock.patch.object(train, "mark_checking") as mc, \
             mock.patch.object(train, "compare", return_value={"commits": [self.commit("x\n\nTouch: #5\n")]}), \
             mock.patch.object(train, "train_pr", return_value={"number": 9, "head": {"sha": "H", "ref": "t"},
                                                                  "base": {"sha": "B"}}), \
             mock.patch.object(train, "rollup", return_value=([1], [], [], [])), \
             mock.patch.object(train, "run", return_value=_proc()), \
             mock.patch.object(train, "api"), \
             mock.patch.object(train, "should_cancel_main_run", return_value=False), \
             contextlib.redirect_stdout(io.StringIO()):
            train.train_step(self.REPO, self.SIGN)
        mc.assert_called_once_with(self.REPO, {5}, self.SIGN, "H")


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
                mock.patch.object(train, "complaints_warn"), \
                contextlib.redirect_stdout(io.StringIO()) as out:
            rc = train.tick_all("sig")
        self.assertEqual(calls, ["o/a", "o/b"])
        self.assertEqual(rc, 1)
        self.assertIn("ОШИБКА tick o/a", out.getvalue())


class ComplaintsWarnTest(unittest.TestCase):
    NOW = datetime(2026, 10, 14, 18, 0, tzinfo=timezone.utc)

    def run_warn(self, prs):
        out = io.StringIO()
        with mock.patch.object(train, "api", return_value=prs), contextlib.redirect_stdout(out):
            train.complaints_warn("o/acct", now=self.NOW)
        return out.getvalue()

    def pr(self, n, ref, created):
        return {"number": n, "head": {"ref": ref}, "created_at": created}

    def test_old_complaint_prs_are_listed(self):
        out = self.run_warn([self.pr(5, "complaint/x", "2026-10-14T10:00:00Z"),
                             self.pr(6, "complaint/y", "2026-10-14T16:00:00Z"),
                             self.pr(7, "lunobot/urgent/z", "2026-10-13T10:00:00Z")])
        self.assertIn("1 PR жалоб", out)
        self.assertIn("#5", out)
        self.assertNotIn("#6", out)
        self.assertNotIn("#7", out)

    def test_malformed_api_answer_is_silent(self):
        self.assertEqual(self.run_warn([{"number": 5, "head": {"ref": "complaint/x"}}]), "")
        self.assertEqual(self.run_warn({"message": "Not Found"}), "")

    def test_tick_all_calls_warn_without_changing_rc(self):
        with mock.patch.object(train, "staged_repos", return_value=["o/a"]), \
                mock.patch.object(train, "tick", return_value=0), \
                mock.patch.object(train, "dispatch_format_warn"), \
                mock.patch.object(train, "complaints_warn") as warn, \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(train.tick_all("sig"), 0)
        warn.assert_called_once_with()

    def test_nothing_printed_when_all_fresh_or_api_fails(self):
        self.assertEqual(self.run_warn([self.pr(6, "complaint/y", "2026-10-14T16:00:00Z")]), "")
        self.assertEqual(self.run_warn(None), "")


class LandCommitParseTest(unittest.TestCase):
    def test_strips_git_log_separator_newline_from_later_sha(self):
        first = "a" * 40
        second = "b" * 40
        output = f"{first}\0first body\x01\n{second}\0second body\x01\n"
        self.assertEqual(train.parse_land_commits(output), [
            (first, "first body"), (second, "second body")])


class HealedByRevertTest(unittest.TestCase):
    URL = "https://github.com/unxed/f4/actions/runs/39017396343"

    def test_fix_after_revert_of_same_run_is_refused(self):
        fix = [f"test fix\n\nFixes-Staging: {self.URL}\n"]
        log = [f'Revert "x"\n\nStaging-Revert: {self.URL}\n', "other\n"]
        self.assertEqual(train.healed_by_revert(fix, log), self.URL)

    def test_fix_of_other_run_or_without_revert_is_fine(self):
        fix = [f"fix\n\nFixes-Staging: {self.URL}\n"]
        self.assertIsNone(train.healed_by_revert(fix, ["Staging-Revert: https://x/runs/1\n"]))
        self.assertIsNone(train.healed_by_revert(fix, ["plain commit\n"]))
        self.assertIsNone(train.healed_by_revert(["no trailer\n"], [f"Staging-Revert: {self.URL}\n"]))


class MainHelpTest(unittest.TestCase):
    """5а.1: `--help` и опечатка в аргументах не должны запускать настоящий land."""

    def run_main(self, argv):
        out = io.StringIO()
        with mock.patch.object(train, "land", return_value=0) as land, \
                contextlib.redirect_stdout(out):
            rc = train.main(argv)
        return rc, land, out.getvalue()

    def test_land_help_does_nothing(self):
        for argv in (["land", "--help"], ["land", "-h"], ["--help"], ["help"]):
            rc, land, out = self.run_main(argv)
            self.assertEqual(rc, 0, argv)
            land.assert_not_called()
            self.assertIn("train.py land", out)

    def test_other_commands_help_does_not_run(self):
        with mock.patch.object(train, "tick") as tick, \
                mock.patch.object(train, "health") as health, \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(train.main(["tick", "unxed/f4", "--help"]), 0)
            self.assertEqual(train.main(["health", "-h"]), 0)
        tick.assert_not_called()
        health.assert_not_called()

    def test_land_unknown_argument_refused(self):
        rc, land, out = self.run_main(["land", "--fix-stagin"])
        self.assertEqual(rc, 2)
        land.assert_not_called()
        self.assertIn("--fix-staging", out)

    def test_land_known_flags_still_work(self):
        rc, land, _ = self.run_main(["land"])
        land.assert_called_once_with(fix=False)
        land.reset_mock()
        rc, land, _ = self.run_main(["land", "--fix-staging"])
        land.assert_called_once_with(fix=True)


class DepsSandboxTest(unittest.TestCase):
    """Коммит с go.mod/go.sum приземляется только после полного прогона песочницы (§ 7.2)."""

    REPO = "unxed/f4"
    BODY = "bump vtui\n\nLunobot-Task: vtui-bump\nSandbox-Full: https://github.com/unxed/f4/actions/runs/777\n"
    GOOD = {"status": "completed", "conclusion": "success", "event": "workflow_dispatch",
            "path": ".github/workflows/sandbox.yml", "head_sha": "a" * 40}

    def problem(self, body=None, run_json=None, mine="p1", theirs="p1", fetch_rc=0):
        fetched = mock.Mock(returncode=fetch_rc)
        with mock.patch.object(train, "api", return_value=run_json), \
                mock.patch.object(train, "run", return_value=fetched), \
                mock.patch.object(train, "patch_id", side_effect=[mine, theirs]):
            return train.deps_sandbox_problem(self.REPO, "b" * 40, body or self.BODY)

    def test_only_root_module_files_count(self):
        self.assertTrue(train.touches_deps(["go.mod", "x.go"]))
        self.assertTrue(train.touches_deps(["go.sum"]))
        self.assertFalse(train.touches_deps(["plugins/android/go.mod", "flake.nix"]))
        self.assertFalse(train.touches_deps([]))

    def test_missing_trailer_is_refused(self):
        self.assertIn("Sandbox-Full", self.problem(body="bump\n\nLunobot-Task: x\n"))

    def test_green_run_on_same_patch_passes(self):
        self.assertIsNone(self.problem(run_json=self.GOOD))

    def test_foreign_repository_is_refused(self):
        body = self.BODY.replace("unxed/f4", "unxed/vtui")
        self.assertIn("чужого репозитория", self.problem(body=body, run_json=self.GOOD))

    def test_repository_name_is_case_insensitive(self):
        body = self.BODY.replace("unxed/f4", "Unxed/F4")
        self.assertIsNone(self.problem(body=body, run_json=self.GOOD))

    def test_unknown_run_is_refused(self):
        self.assertIn("не найден", self.problem(run_json={"message": "Not Found"}))
        self.assertIn("не найден", self.problem(run_json=None))

    def test_not_a_sandbox_dispatch_is_refused(self):
        quick = dict(self.GOOD, event="push", path=".github/workflows/quick.yml")
        self.assertIn("не sandbox.yml", self.problem(run_json=quick))

    def test_red_or_running_run_is_refused(self):
        for conclusion, status in (("failure", "completed"), (None, "in_progress")):
            run_json = dict(self.GOOD, conclusion=conclusion, status=status)
            self.assertIn("не зелёный", self.problem(run_json=run_json))

    def test_run_on_other_patch_is_refused(self):
        self.assertIn("другим патчем", self.problem(run_json=self.GOOD, theirs="p2"))
        self.assertIn("другим патчем", self.problem(run_json=self.GOOD, mine=None, theirs=None))

    def test_unfetchable_tested_commit_is_refused(self):
        self.assertIn("не удалось получить", self.problem(run_json=self.GOOD, fetch_rc=1))


class PatchIdTest(unittest.TestCase):
    """patch-id не зависит от сообщения и от базы: так land узнаёт код, прошедший песочницу."""

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.dir, check=True, capture_output=True,
                              text=True).stdout.strip()

    def test_same_change_on_another_base_and_message(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            self.dir = d
            self.git("init", "-q", "-b", "main")
            self.git("config", "user.email", "t@example.com")
            self.git("config", "user.name", "t")
            for name in ("a", "go.mod"):
                with open(os.path.join(d, name), "w") as f:
                    f.write("one\n")
            self.git("add", ".")
            self.git("commit", "-q", "-m", "base")
            self.git("switch", "-q", "-c", "work")
            with open(os.path.join(d, "go.mod"), "w", encoding="utf-8") as f:
                f.write("два Н\n")
            self.git("commit", "-q", "-am", "bump")
            tested = self.git("rev-parse", "HEAD")
            self.git("switch", "-q", "main")
            with open(os.path.join(d, "a"), "w") as f:
                f.write("moved\n")
            self.git("commit", "-q", "-am", "base moved")
            self.git("cherry-pick", "-x", tested)
            self.git("commit", "-q", "--amend", "-m", "bump\n\nSandbox-Full: https://x")
            landed = self.git("rev-parse", "HEAD")
            self.assertNotEqual(tested, landed)
            old = os.getcwd()
            os.chdir(d)
            try:
                self.assertIsNotNone(train.patch_id(tested))
                self.assertEqual(train.patch_id(tested), train.patch_id(landed))
                self.assertNotEqual(train.patch_id(tested), train.patch_id(self.git("rev-parse", "HEAD~1")))
                self.assertIsNone(train.patch_id("0" * 40))
            finally:
                os.chdir(old)


# Фрагменты РЕАЛЬНЫХ логов упавших job'ов `Test (darwin/arm64 rest)` unxed/f4 (сырой лог REST
# `actions/jobs/<id>/logs`, 16-10-2026): job 117021805635 (поезд unxed/f4#1996, internal/media)
# и job 117003963953 (поезд unxed/f4#1995, internal/app; вывод теста с управляющими
# последовательностями терминала).
MEDIA_LOG = """\
2026-10-16T14:27:19.3866400Z ok  \tgithub.com/unxed/f4/internal/keymap\t0.313s\tcoverage: 0.7% of statements in ./...
2026-10-16T14:27:19.3870070Z ok  \tgithub.com/unxed/f4/internal/macro\t2.635s\tcoverage: 1.5% of statements in ./...
2026-10-16T14:27:19.3872710Z -test.shuffle 1792160756767382000
2026-10-16T14:27:19.3873430Z --- FAIL: TestImageViewRequestThumbGivesUpWhenDecodeFails (0.02s)
2026-10-16T14:27:19.3875490Z     image_gallery_coverage_test.go:266: a failed decode must not post a tile to the UI thread
2026-10-16T14:27:19.3897730Z FAIL
2026-10-16T14:27:19.3898280Z coverage: 1.8% of statements in ./...
2026-10-16T14:27:19.3899090Z FAIL\tgithub.com/unxed/f4/internal/media\t1.218s
2026-10-16T14:27:19.3902520Z ok  \tgithub.com/unxed/f4/internal/menuhotkeys\t0.432s\tcoverage: 0.1% of statements in ./...
2026-10-16T14:27:56.4454340Z FAIL
2026-10-16T14:27:56.8564990Z ##[error]Process completed with exit code 1.
"""
APP_LOG = """\
2026-10-16T13:47:06.8663470Z ok  \tgithub.com/unxed/f4/cmd/f4\t6.893s\tcoverage: 0.7% of statements in ./...
2026-10-16T13:47:06.8764930Z \tgithub.com/unxed/f4/cmd/f4-gui-launcher\t\tok  \tgithub.com/unxed/f4/internal/action\t0.252s\tcoverage: 0.0% of statements in ./... [no tests to run]
2026-10-16T13:49:02.2967360Z -test.shuffle 1792158441088954000
2026-10-16T13:49:02.2984870Z \x1b[?1049h\x1b[2J\x1b[H\x1b[?1049l\x1b[?1049h\x1b[2J\x1b[H--- FAIL: TestEditorCtrlOAfterCtrlTabStillRestoresPanels (0.01s)
2026-10-16T13:49:02.2987370Z     editor_actions_test.go:363: second Ctrl+O from the editor: workspace 1, ShowPanels=true
2026-10-16T13:49:02.2991630Z \x1b[?1049h\x1b[2J\x1b[H\x1b[?7l\x1b[8l\x1b[1 k\x1b[?1049lFAIL
2026-10-16T13:49:02.2993190Z coverage: 23.4% of statements in ./...
2026-10-16T13:49:02.2995180Z FAIL\tgithub.com/unxed/f4/internal/app\t101.405s
2026-10-16T13:49:02.2996500Z ?   \tgithub.com/unxed/f4/internal/appcmd\t[no test files]
"""


class FailedSeedsTest(unittest.TestCase):
    def test_package_and_seed_of_failed_package(self):
        self.assertEqual(train.failed_seeds(MEDIA_LOG, "unxed/f4"),
                         [("./internal/media", "1792160756767382000")])

    def test_terminal_escapes_and_interleaved_lines(self):
        self.assertEqual(train.failed_seeds(APP_LOG, "unxed/f4"),
                         [("./internal/app", "1792158441088954000")])

    def test_gh_run_view_log_prefix(self):
        cli = "".join(f"Test (darwin/arm64 rest)\tUNKNOWN STEP\t{line}\n"
                      for line in MEDIA_LOG.splitlines())
        self.assertEqual(train.failed_seeds(cli, "unxed/f4"),
                         [("./internal/media", "1792160756767382000")])

    def test_log_without_timestamps(self):
        bare = "ok  \tgithub.com/o/r/a\t0.1s\n-test.shuffle 7\n--- FAIL: TestX (0s)\nFAIL\nFAIL\tgithub.com/o/r/b\t0.2s\n"
        self.assertEqual(train.failed_seeds(bare, "o/r"), [("./b", "7")])

    def test_several_failed_packages_get_their_own_seeds(self):
        log = ("-test.shuffle 1\nFAIL\nFAIL\tgithub.com/o/r/a\t1s\n"
               "ok  \tgithub.com/o/r/b\t1s\n"
               "-test.shuffle 2\nFAIL\nFAIL\tgithub.com/o/r/c/d\t1s\n"
               "-test.shuffle 3\nFAIL\nFAIL\tgithub.com/o/r\t1s\n")
        self.assertEqual(train.failed_seeds(log, "o/r"),
                         [("./a", "1"), ("./c/d", "2"), (".", "3")])

    def test_seed_of_green_package_does_not_leak_to_next_failure(self):
        # `go test -v`: зелёный пакет тоже печатает seed; у упавшего без seed (сборка) его нет.
        log = "-test.shuffle 5\nok  \tgithub.com/o/r/a\t1s\nFAIL\tgithub.com/o/r/b [build failed]\n"
        self.assertEqual(train.failed_seeds(log, "o/r"), [])

    def test_no_seed_or_foreign_package_means_no_seeds(self):
        self.assertEqual(train.failed_seeds("FAIL\tgithub.com/o/r/a\t1s\n", "o/r"), [])
        self.assertEqual(
            train.failed_seeds("-test.shuffle 5\nFAIL\tgithub.com/other/mod/a\t1s\n", "o/r"), [])
        self.assertEqual(
            train.failed_seeds("-test.shuffle 5\nFAIL\tgithub.com/o/rx/a\t1s\n", "o/r"), [])

    def test_green_log(self):
        self.assertEqual(train.failed_seeds("ok  \tgithub.com/o/r/a\t1s\n", "o/r"), [])


class SeededBisectCommandTest(unittest.TestCase):
    JOB = "Test (darwin/arm64 rest)"
    URL = "https://github.com/unxed/f4/actions/runs/38913158596/job/117021805635"

    def test_run_tests_uses_the_seed_of_the_failed_package(self):
        steps = [(self.JOB, "Run Tests")]
        seeds = {self.JOB: [("./internal/media", "1792160756767382000")]}
        self.assertEqual(
            train.pick_target_steps(steps, seeds),
            ("macos-latest", "go test -count=1 -shuffle=1792160756767382000 ./internal/media"))

    def test_race_detector_keeps_race_and_one_command_per_package(self):
        steps = [("Race", "Run race detector")]
        seeds = {"Race": [("./a", "1"), ("./b", "2")]}
        self.assertEqual(
            train.pick_target_steps(steps, seeds),
            ("ubuntu-latest",
             "go test -race -count=1 -shuffle=1 ./a && go test -race -count=1 -shuffle=2 ./b"))

    def test_without_seeds_the_old_command(self):
        steps = [(self.JOB, "Run Tests")]
        self.assertEqual(train.pick_target_steps(steps),
                         ("macos-latest", "go test -count=1 ./..."))
        self.assertEqual(train.pick_target_steps(steps, {}),
                         ("macos-latest", "go test -count=1 ./..."))

    def test_seeds_do_not_touch_other_steps_or_unknown_steps(self):
        seeds = {"Test (x)": [("./a", "1")]}
        self.assertEqual(train.pick_target_steps([("Test (x)", "Test")], seeds),
                         ("ubuntu-latest", "go test -count=1 -timeout 4m ./..."))
        self.assertIsNone(train.pick_target_steps([("Test (x)", "Unknown step")], seeds))

    def test_seeds_are_read_from_the_log_of_the_failed_job_only(self):
        failed = [{"name": self.JOB, "detailsUrl": self.URL},
                  {"name": "Lint", "detailsUrl": self.URL.replace("117021805635", "1")}]
        steps = [(self.JOB, "Run Tests"), ("Lint", "Check formatting")]
        with mock.patch.object(train, "job_log", return_value=MEDIA_LOG) as log:
            seeds = train.bisect_seeds("unxed/f4", failed, steps)
        log.assert_called_once_with("unxed/f4", "117021805635")
        self.assertEqual(seeds, {self.JOB: [("./internal/media", "1792160756767382000")]})

    def test_no_log_means_no_seeds(self):
        failed = [{"name": self.JOB, "detailsUrl": self.URL}]
        with mock.patch.object(train, "job_log", return_value=None):
            self.assertEqual(train.bisect_seeds("unxed/f4", failed, [(self.JOB, "Run Tests")]), {})

    def test_job_log_retries_without_flag_on_old_gh(self):
        calls = []

        def run(*args, **kwargs):
            calls.append(args)
            if "--allow-escape-sequences" in args:
                return subprocess.CompletedProcess(args, 1, "", "unknown flag: --allow-escape-sequences")
            return subprocess.CompletedProcess(args, 0, "LOG", "")

        with mock.patch.object(train, "run", side_effect=run):
            self.assertEqual(train.job_log("o/r", "5"), "LOG")
        self.assertEqual(calls[-1], ("gh", "api", "repos/o/r/actions/jobs/5/logs"))

    def test_job_log_gives_up_on_other_errors(self):
        with mock.patch.object(train, "run", return_value=subprocess.CompletedProcess(
                (), 1, "", "HTTP 404")) as r:
            self.assertIsNone(train.job_log("o/r", "5"))
        self.assertEqual(r.call_count, 1)


# Строка шага «Run Tests» f4 из начала лога job'а 117021805635 (сырой лог REST, escape-цвета как есть).
STEP_LINE = ("2026-10-16T14:25:01.5307820Z \x1b[36;1mgo test \"${cover_args[@]}\" -shuffle=\"$TEST_SHUFFLE\" "
             "-timeout 15m -skip '^TestAllDialogs_LayoutValidation$' \"${run_args[@]}\" \"${targets[@]}\"\x1b[0m\n")
RACE_LINE = ("2026-10-16T14:25:01.5307820Z go test -race -shuffle=on -timeout 15m "
             "-skip '^TestSeedSweep$' \"${packages[@]}\"\n")


class LogTestFlagsTest(unittest.TestCase):
    def test_timeout_and_skip_of_the_ci_step(self):
        self.assertEqual(train.log_test_flags(STEP_LINE + MEDIA_LOG),
                         "-timeout 15m -skip '^TestAllDialogs_LayoutValidation$'")
        self.assertEqual(train.log_test_flags(RACE_LINE), "-timeout 15m -skip '^TestSeedSweep$'")

    def test_cli_prefix(self):
        cli = "".join(f"Test (x)\tUNKNOWN STEP\t{line}\n" for line in STEP_LINE.splitlines())
        self.assertEqual(train.log_test_flags(cli),
                         "-timeout 15m -skip '^TestAllDialogs_LayoutValidation$'")

    def test_only_the_shuffled_go_test_line_counts(self):
        # отдельный прогон `go test -v -run …` в том же скрипте без -shuffle — не тот
        other = "go test -v -count=1 -timeout 5m -skip 'x' -run '^T$' ./internal/app\n"
        self.assertEqual(train.log_test_flags(other + MEDIA_LOG), "")

    def test_unsafe_regex_is_dropped(self):
        for rx in ("a b", "a*", "a[0-9]", "a;b"):
            line = f"go test -shuffle=on -skip '{rx}' ./...\n"
            self.assertNotIn("-skip", train.log_test_flags(line), rx)

    def test_seeded_command_carries_the_flags(self):
        self.assertEqual(
            train.seeded_cmd("Run Tests", [("./internal/app", "7", "-timeout 15m -skip '^T$'")]),
            "go test -count=1 -timeout 15m -skip '^T$' -shuffle=7 ./internal/app")
        self.assertEqual(train.seeded_cmd("Run Tests", [("./a", "7")]),
                         "go test -count=1 -shuffle=7 ./a")

    def test_bisect_seeds_adds_the_flags_from_the_log(self):
        job = "Test (darwin/arm64 rest)"
        failed = [{"name": job, "detailsUrl": SeededBisectCommandTest.URL}]
        with mock.patch.object(train, "job_log", return_value=STEP_LINE + MEDIA_LOG):
            seeds = train.bisect_seeds("unxed/f4", failed, [(job, "Run Tests")])
        self.assertEqual(
            train.pick_target_steps([(job, "Run Tests")], seeds),
            ("macos-latest", "go test -count=1 -timeout 15m -skip '^TestAllDialogs_LayoutValidation$' "
                             "-shuffle=1792160756767382000 ./internal/media"))


class ReadsCloseFilesTest(unittest.TestCase):
    """Чтение TRIAGE.md и projects/*.md не оставляет открытых дескрипторов (ResourceWarning)."""

    def resource_warnings(self, func):
        import gc
        import warnings

        with warnings.catch_warnings(record=True) as seen:
            warnings.simplefilter("always", ResourceWarning)
            func()
            gc.collect()
        return [w for w in seen if issubclass(w.category, ResourceWarning)]

    def test_transit_warn_read_closes_file(self):
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "TRIAGE.md")
            with open(path, "w", encoding="utf-8") as f:
                f.write("| 7 | 3 | свободен | 1 | 2026-10-16T01:00:00Z |\n")
            with mock.patch.object(train, "triage_path", return_value=path):
                self.assertEqual(self.resource_warnings(lambda: train.transit_warn("unxed/f4")), [])

    def test_staged_repos_read_closes_files(self):
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "projects")
            os.makedirs(os.path.join(root, "f4"))
            with open(os.path.join(root, "INDEX.md"), "w", encoding="utf-8") as f:
                f.write("1. [f4](f4/PROJECT.md)\n2. [нет](нет/PROJECT.md)\n")
            with open(os.path.join(root, "f4", "PROJECT.md"), "w", encoding="utf-8") as f:
                f.write("- Код: https://github.com/unxed/f4\n")
            result = []
            with mock.patch.object(train, "__file__", os.path.join(tmp, "train.py")), \
                 mock.patch.object(train, "api", return_value={"commit": {}}):
                seen = self.resource_warnings(lambda: result.extend(train.staged_repos()))
            self.assertEqual(seen, [])
            self.assertEqual(result, ["unxed/f4"])


class RevertedLaterInTrainTest(unittest.TestCase):
    def test_revert_after_step_is_found(self):
        a, b, c = "a" * 40, "b" * 40, "c" * 40
        commits = [
            {"sha": a, "commit": {"message": "step"}},
            {"sha": b, "commit": {"message": f'Revert "step"\n\nThis reverts commit {a}.\n'}},
            {"sha": c, "commit": {"message": "step again"}},
        ]
        self.assertEqual(train.reverted_later_in_train(commits, 0), b)

    def test_no_revert_means_none(self):
        a, b = "a" * 40, "b" * 40
        commits = [{"sha": a, "commit": {"message": "step"}}, {"sha": b, "commit": {"message": "other"}}]
        self.assertIsNone(train.reverted_later_in_train(commits, 0))

    def test_revert_before_step_is_ignored(self):
        a, b = "a" * 40, "b" * 40
        commits = [{"sha": b, "commit": {"message": f"This reverts commit {a}."}},
                   {"sha": a, "commit": {"message": "step"}}]
        self.assertIsNone(train.reverted_later_in_train(commits, 1))
