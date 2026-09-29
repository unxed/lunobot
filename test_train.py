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


if __name__ == "__main__":
    unittest.main()
