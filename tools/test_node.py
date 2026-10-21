import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import node


class NodeTest(unittest.TestCase):
    def test_linux_machine_id_trailing_newline_does_not_change_node(self):
        with tempfile.TemporaryDirectory() as directory:
            machine_id = Path(directory, "machine-id")
            machine_id.write_text("abc123\n", encoding="utf-8")
            self.assertEqual(node.identify("linux", str(machine_id)), node.digest("abc123"))
            self.assertEqual(node.digest("abc123\n"), node.digest("abc123"))

    def test_digest_uses_utf8_and_first_24_lowercase_hex(self):
        self.assertRegex(node.digest("пример"), r"^[0-9a-f]{24}$")

    def test_macos_reads_ioplatform_uuid(self):
        output = '    "IOPlatformUUID" = "abc-123"\n'
        with patch.object(node.subprocess, "check_output", return_value=output):
            self.assertEqual(node.identify("darwin"), node.digest("abc-123"))

    def test_bsd_reads_hostuuid(self):
        with patch.object(node.subprocess, "check_output", return_value="abc-123\n") as run:
            self.assertEqual(node.identify("freebsd14"), node.digest("abc-123"))
        run.assert_called_once_with(["sysctl", "-n", "kern.hostuuid"], text=True)


if __name__ == "__main__":
    unittest.main()
