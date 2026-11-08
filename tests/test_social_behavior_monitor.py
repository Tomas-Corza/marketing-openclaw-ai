"""Offline tests: run with python3 -m unittest discover -s tests."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from social_behavior_monitor import aggregate, analyze, read_records


class SocialBehaviorMonitorTests(unittest.TestCase):
    def test_example(self):
        path = Path(__file__).resolve().parents[1] / "examples/social_behavior_sample.csv"
        result = analyze(read_records(str(path)))
        self.assertEqual(result["overall"]["content_count"], 3)
        self.assertEqual(result["by_platform"]["instagram"]["content_count"], 2)
        self.assertIn("youtube", result["by_platform"])

    def test_missing_denominator(self):
        rows = [{"impressions": None, "likes": 1, "comments": 2, "shares": 0, "saves": 0, "clicks": 0,
                 "views": None, "reach": None}]
        self.assertIsNone(aggregate(rows)["engagement_per_impression"])

    def test_negative_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.csv"
            path.write_text("platform,content_id,published_at,impressions,likes,comments,shares,saves,clicks\ninstagram,1,2026-01-01,10,-1,0,0,0,0\n")
            with self.assertRaisesRegex(ValueError, "nonnegative"):
                read_records(str(path))


if __name__ == "__main__":
    unittest.main()
