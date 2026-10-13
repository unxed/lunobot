"""Tests for fetch_images.py's per-instance output directory."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import fetch_images


class ImageDirectoryTest(unittest.TestCase):
    def test_uses_the_bot_directory_containing_accounting(self):
        with TemporaryDirectory() as directory:
            bot_dir = Path(directory) / "lunobot-42"
            script = bot_dir / "accounting" / "fetch_images.py"
            path = fetch_images.image_directory("unxed/f4", 1389, str(script))
        self.assertEqual(Path(path), bot_dir / "img" / "unxed-f4-1389")


if __name__ == "__main__":
    unittest.main()
