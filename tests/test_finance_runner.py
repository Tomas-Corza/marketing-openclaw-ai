"""Smoke tests for the scheduled synthetic runner."""
import json
from pathlib import Path
import tempfile
import unittest
from finance.automation_runner import run

class FinanceRunnerTests(unittest.TestCase):
    def test_writes_private_results_and_log(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            result = run(out)
            self.assertEqual(result["source"], "synthetic")
            self.assertTrue(result["read_only"])
            self.assertIn("summary", json.loads((out / "latest.json").read_text()))
            self.assertEqual(len((out / "runs.jsonl").read_text().splitlines()), 1)
            self.assertEqual((out / "latest.json").stat().st_mode & 0o777, 0o600)

    def test_rejects_unimplemented_live_mode(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                run(Path(d), "live")

if __name__ == "__main__":
    unittest.main()
