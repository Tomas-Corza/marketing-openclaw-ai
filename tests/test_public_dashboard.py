"""Smoke-test Streamlit public demo without any merchant credentials."""
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]

class PublicDashboardTests(unittest.TestCase):
    def test_public_demo_renders_without_uploaders(self):
        app = AppTest.from_file(str(ROOT / "dashboard" / "public_app.py"), default_timeout=35).run()
        self.assertFalse(app.exception, [e.message for e in app.exception])
        self.assertEqual(len(app.get("file_uploader")), 0)
        self.assertGreaterEqual(len(app.tabs), 5)
        self.assertGreater(len(app.info), 0)

if __name__ == "__main__":
    unittest.main()
