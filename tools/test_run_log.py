import unittest

import run_log


class CleanTest(unittest.TestCase):
    def test_strips_escapes_stamp_and_bom(self):
        raw = "﻿2026-10-17T05:03:23.6815490Z \x1b[36;1mok\x1b[0m  pkg\n2026-10-17T05:03:24.0000000Z plain\nno stamp"
        self.assertEqual(run_log.clean(raw), ["ok  pkg", "plain", "no stamp"])


if __name__ == "__main__":
    unittest.main()
