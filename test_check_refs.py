import os
import tempfile
import unittest

import check_refs


class CheckRefsTest(unittest.TestCase):
    def setUp(self):
        self.known = check_refs.sections("## 8. Учётные записи\n### 8.1 Уборка\n## 9. Как писать\n")

    def write(self, text):
        fd, path = tempfile.mkstemp(suffix=".md")
        os.close(fd)
        self.addCleanup(os.unlink, path)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    def test_sections_found(self):
        self.assertEqual(self.known, {"8", "8.1", "9"})

    def test_existing_ref_ok(self):
        path = self.write("# DISPATCH — x\n\nФормат — § 8 инструкции.\n")
        self.assertEqual(check_refs.check(path, self.known), [])

    def test_missing_ref_reported(self):
        path = self.write("# DISPATCH — x\n\nФормат — § 14.1 инструкции.\n")
        self.assertEqual(check_refs.check(path, self.known), [(3, "14.1")])

    def test_refs_below_header_ignored(self):
        path = self.write("# x\n\n\n\n\n\n14-10-2026 запись по § 99\n")
        self.assertEqual(check_refs.check(path, self.known), [])


if __name__ == "__main__":
    unittest.main()
