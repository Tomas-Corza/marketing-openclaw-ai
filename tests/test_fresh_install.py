"""Offline deployment tests; do not install OpenClaw or touch the real workspace."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from setup_skills import install, names
from verify_installation import verify


class FreshInstallTests(unittest.TestCase):
    def test_skills_count(self):
        skills = names()
        self.assertEqual(len(skills), 12)
        self.assertIn("shopify-return-processing", skills)
        self.assertIn("gmail-customer-inquiry-drafts", skills)

    def test_dry_run_is_read_only(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "workspace"
            result = install(target, dry_run=True)
            self.assertGreater(result["new_files"], 0)
            self.assertFalse(target.exists())

    def test_install_repeat_and_verify(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "workspace"
            first = install(target)
            second = install(target)
            self.assertGreater(first["new_files"], 0)
            self.assertEqual(second["new_files"], 0)
            self.assertTrue(verify(target, check_openclaw=False)["passed"])

    def test_conflicts_prevent_any_changes(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "workspace"
            (target / "skills" / "shopify-return-processing").mkdir(parents=True)
            collision = target / "skills" / "shopify-return-processing" / "SKILL.md"
            collision.write_text("customized version")
            with self.assertRaisesRegex(ValueError, "Conflicts"):
                install(target)
            self.assertEqual(collision.read_text(), "customized version")
            self.assertFalse((target / "tools").exists())

    def test_symlink_parent_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "workspace"
            target.mkdir()
            (target / "skills").symlink_to(Path(d))
            with self.assertRaisesRegex(ValueError, "Conflicts"):
                install(target)
            self.assertFalse((target / "tools").exists())


if __name__ == "__main__":
    unittest.main()
