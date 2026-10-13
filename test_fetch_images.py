import tempfile
import unittest
from pathlib import Path

import fetch_images


class ImageOutputDirTest(unittest.TestCase):
    def test_uses_workdir_of_its_own_lunobot_clone(self):
        with tempfile.TemporaryDirectory() as tmp:
            bot_root = Path(tmp) / "lunobot-2"
            accounting = bot_root / "accounting"
            accounting.mkdir(parents=True)
            script = accounting / "fetch_images.py"

            first = Path(fetch_images.image_output_dir(script, "unxed/f4", "1389"))
            second = Path(fetch_images.image_output_dir(script, "unxed/f4", "1389"))

            self.assertEqual(first.parent, bot_root / "work")
            self.assertEqual(second.parent, bot_root / "work")
            self.assertNotEqual(first, second)

    def test_rejects_accounting_clone_outside_lunobot_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            accounting = Path(tmp) / "accounting"
            accounting.mkdir()
            with self.assertRaisesRegex(ValueError, "not under /tmp/lunobot"):
                fetch_images.image_output_dir(accounting / "fetch_images.py", "unxed/f4", "1389")


if __name__ == "__main__":
    unittest.main()
