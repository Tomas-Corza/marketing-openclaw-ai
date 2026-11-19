import unittest
from datetime import date
from finance.engine import seed_data, analyze, suggest_actions

class FinanceEngineTests(unittest.TestCase):
    def setUp(self):
        self.data=seed_data(date(2026,11,19))
        self.result=analyze(self.data,date(2026,11,19))
    def test_expected_balances(self):
        self.assertEqual(self.result["summary"]["ar_outstanding"],21900.0)
        self.assertEqual(self.result["summary"]["ap_open_unique"],6960.0)
    def test_flags_duplicates_variances_and_unapproved_time(self):
        reasons=" ".join(x["reason"] for x in self.result["exceptions"])
        self.assertIn("Duplicate",reasons)
        self.assertIn("PO amount",reasons)
        self.assertIn("Bank",reasons)
        self.assertIn("approved",reasons)
    def test_does_not_emit_executable_payments(self):
        for task in suggest_actions(self.result):
            self.assertEqual(task["execution"],"Review only; no financial writes")
    def test_synthetic_summary_is_deterministic(self):
        self.assertEqual(self.result,analyze(self.data,date(2026,11,19)))

if __name__ == "__main__":
    unittest.main()
