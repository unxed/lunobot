import tempfile
import unittest
from pathlib import Path

import fetch_images


class ImageOutputDirTest(unittest.TestCase):
    def test_manager_clone_gets_unique_dir_in_own_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            bot_root = Path(tmp) / "lunobot-2"
            accounting = bot_root / "accounting"
            accounting.mkdir(parents=True)
            script = accounting / "fetch_images.py"

            first = Path(fetch_images.image_output_dir(script, "unxed/f4", "1389"))
            second = Path(fetch_images.image_output_dir(script, "unxed/f4", "1389"))

            self.assertEqual(first.parent, bot_root.resolve() / "work")
            self.assertEqual(second.parent, bot_root.resolve() / "work")
            self.assertTrue(first.name.startswith("img-unxed-f4-1389-"))
            self.assertNotEqual(first, second)

    def test_worker_clone_writes_into_its_step_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            step = Path(tmp) / "lunobot-2" / "work" / "1389-1014-1200"
            accounting = step / "accounting"
            accounting.mkdir(parents=True)

            path = Path(fetch_images.image_output_dir(accounting / "fetch_images.py", "unxed/f4", "1389"))

            self.assertEqual(path, step.resolve() / "img" / "unxed-f4-1389")
            self.assertTrue(path.is_dir())

    def test_explicit_out_dir_wins(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "lunobot-2" / "work" / "slug" / "img"
            script = Path(tmp) / "elsewhere" / "fetch_images.py"

            path = fetch_images.image_output_dir(script, "unxed/f4", "1389", str(out))

            self.assertEqual(Path(path), out)
            self.assertTrue(out.is_dir())

    def test_rejects_script_outside_lunobot_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            accounting = Path(tmp) / "accounting"
            accounting.mkdir()
            with self.assertRaisesRegex(ValueError, "--out-dir"):
                fetch_images.image_output_dir(accounting / "fetch_images.py", "unxed/f4", "1389")

    def test_cli_out_dir_without_value_fails(self):
        with self.assertRaises(SystemExit):
            fetch_images.main(["unxed/f4", "1389", "--out-dir"])


if __name__ == "__main__":
    unittest.main()
