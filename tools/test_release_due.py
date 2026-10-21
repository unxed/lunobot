import unittest

import release_due as rd


class TestReleaseDue(unittest.TestCase):
    def test_last_version_tag_skips_floating(self):
        refs = ["a refs/tags/nightly", "b refs/tags/v0.1.178", "c refs/tags/v0.1.167", "d refs/tags/latest"]
        self.assertEqual(rd.last_version_tag(refs), "v0.1.178")

    def test_prerelease_tag(self):
        self.assertEqual(rd.last_version_tag(["x refs/tags/v2.20-alpha.1"]), "v2.20-alpha.1")
        self.assertEqual(rd.last_version_tag(["x refs/tags/v0.3.0-beta"]), "v0.3.0-beta")

    def test_no_version_tag(self):
        self.assertIsNone(rd.last_version_tag(["x refs/tags/nightly", "y refs/tags/test-1"]))

    def test_threshold(self):
        self.assertTrue(rd.due(20, 0))
        self.assertFalse(rd.due(19, 13.9))
        self.assertTrue(rd.due(1, 14))
        self.assertFalse(rd.due(0, 100))

    def test_has_releases(self):
        self.assertFalse(rd.has_releases("нет"))
        self.assertFalse(rd.has_releases(None))
        self.assertTrue(rd.has_releases("тег v* → workflow"))


if __name__ == "__main__":
    unittest.main()
