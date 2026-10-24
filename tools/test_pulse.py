import unittest
from datetime import datetime, timezone

import pulse

NOW = datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc)
L1, L2 = "Лунобот-1 (node a; LNX)", "Лунобот-2 (node a; LNX)"


def rec(kind, ts, **kw):
    return {"kind": kind, "ts": ts, "id": kw.pop("id", L1), **kw}


class PulseTest(unittest.TestCase):
    def keys(self, recs):
        return [k for k, _ in pulse.alarms(recs, NOW)]

    def test_quiet_fleet_has_no_alarms(self):
        recs = [rec("round", "2026-10-22T10:00:00Z", exit=0), rec("reflection", "2026-10-22T10:30:00Z", friction=[])]
        self.assertEqual(self.keys(recs), [])
        self.assertIn("Тревог нет", pulse.render([]))

    def test_rounds_without_reflection(self):
        recs = [rec("round", f"2026-10-22T0{h}:00:00Z", exit=0) for h in range(4)]
        self.assertIn("no-reflection", self.keys(recs))

    def test_no_reflection_ignores_failed_attempts_and_deduplicates_retries(self):
        recs = []
        for n in range(4):
            recs += [rec("round", f"2026-10-22T0{n + 1}:00:00Z", exit=124, runner="r", round=n),
                     rec("round", f"2026-10-22T0{n + 1}:01:00Z", exit=0, runner="r", round=n)]
        for n in range(4, 12):
            recs.append(rec("round", f"2026-10-22T1{n - 4}:00:00Z", exit=1, runner="r", round=n))
        recs += [rec("reflection", f"2026-10-22T11:{n:02d}:00Z", friction=[]) for n in range(4)]
        self.assertNotIn("no-reflection", self.keys(recs))

    def test_failing_rounds(self):
        recs = [rec("round", f"2026-10-22T1{h}:00:00Z", exit=124, runner="r", model="m") for h in range(3)]
        recs += [rec("reflection", "2026-10-22T11:00:00Z", friction=[])] * 3
        self.assertIn("rounds-failing", self.keys(recs))

    def test_missing_digest_with_active_lunobot1(self):
        recs = [rec("reflection", "2026-10-19T10:00:00Z", friction=[]), rec("round", "2026-10-22T10:00:00Z", exit=0),
                rec("reflection", "2026-10-22T10:10:00Z", friction=[])]
        self.assertIn("no-digest", self.keys(recs))
        recs.append(rec("digest", "2026-10-21T20:00:00Z", until="2026-10-21T20:00:00Z"))
        self.assertNotIn("no-digest", self.keys(recs))

    def test_repeated_friction_since_last_digest(self):
        fr = [{"tag": "push-race", "text": "x"}]
        recs = [rec("digest", "2026-10-22T00:00:00Z")] + [
            rec("reflection", f"2026-10-22T0{h + 1}:00:00Z", friction=fr, id=L2) for h in range(3)]
        self.assertIn("friction-repeats", self.keys(recs))


if __name__ == "__main__":
    unittest.main()
