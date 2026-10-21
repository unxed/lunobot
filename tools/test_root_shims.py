#!/usr/bin/env python3
"""The forwarders in the root of the clone (unxed/lunobot#247): the scripts moved to tools/ on 21-10-2026, and the
root keeps one forwarder per script for the sessions that read the instruction before the move and for the copies of
runners/*.sh on the nodes. Each forwarder must point to its script and run it unchanged. They are removed only by the
owner's decision (then delete the root *.py files and this test)."""
import glob
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


class RootShims(unittest.TestCase):
    def shims(self):
        return sorted(glob.glob(os.path.join(ROOT, "*.py")))

    def test_each_forwarder_has_its_script(self):
        for p in self.shims():
            self.assertTrue(os.path.isfile(os.path.join(HERE, os.path.basename(p))), p)

    def test_forwarder_runs_the_script(self):
        p = os.path.join(ROOT, "node.py")
        if not os.path.isfile(p):
            self.skipTest("no forwarders")
        a = subprocess.run([sys.executable, p], capture_output=True, text=True)
        b = subprocess.run([sys.executable, os.path.join(HERE, "node.py")], capture_output=True, text=True)
        self.assertEqual((a.returncode, a.stdout), (b.returncode, b.stdout))
        self.assertIn("moved to tools/node.py", a.stderr)


if __name__ == "__main__":
    unittest.main()
