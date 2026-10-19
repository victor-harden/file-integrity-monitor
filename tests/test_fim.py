import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import fim


class FimTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "a.txt").write_text("alpha")
        (self.root / "b.txt").write_text("beta")
        (self.root / "sub").mkdir()
        (self.root / "sub" / "c.txt").write_text("gamma")

    def tearDown(self):
        self.tmp.cleanup()

    def test_baseline_counts_files(self):
        data = fim.baseline(self.root)
        self.assertEqual(len(data["files"]), 3)
        self.assertIn("sub/c.txt", data["files"])

    def test_clean_compare(self):
        data = fim.baseline(self.root)
        self.assertTrue(fim.compare(data, fim.baseline(self.root))["clean"])

    def test_change_detected(self):
        data = fim.baseline(self.root)
        (self.root / "a.txt").write_text("changed")
        result = fim.compare(data, fim.baseline(self.root))
        self.assertEqual(result["changed"], ["a.txt"])
        self.assertFalse(result["clean"])

    def test_added_and_removed(self):
        data = fim.baseline(self.root)
        (self.root / "b.txt").unlink()
        (self.root / "new.txt").write_text("new")
        result = fim.compare(data, fim.baseline(self.root))
        self.assertEqual(result["added"], ["new.txt"])
        self.assertEqual(result["removed"], ["b.txt"])

    def test_excludes_patterns(self):
        (self.root / "debug.log").write_text("noise")
        data = fim.baseline(self.root)
        self.assertNotIn("debug.log", data["files"])

    def test_render_clean(self):
        self.assertEqual(fim.render({"added": [], "removed": [], "changed": [], "clean": True}),
                         "no changes detected")

    def test_render_changes(self):
        text = fim.render({"added": ["x"], "removed": [], "changed": ["y"], "clean": False})
        self.assertIn("added    x", text)
        self.assertIn("changed  y", text)

    def test_cli_baseline_and_verify(self):
        import contextlib
        import io
        with tempfile.TemporaryDirectory() as tmp:
            baseline_path = Path(tmp) / "baseline.json"
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                code = fim.main(["baseline", str(self.root), "--out", str(baseline_path)])
                verify_code = fim.main(["verify", str(self.root), "--baseline",
                                        str(baseline_path)])
            self.assertEqual(code, 0)
            self.assertEqual(verify_code, 0)
            self.assertTrue(json.loads(baseline_path.read_text())["files"])


if __name__ == "__main__":
    unittest.main()
