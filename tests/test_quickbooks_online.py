import unittest
from finance.quickbooks_online import (
    QBOReadOnlyClient, prepare_payroll_review,
    summarize_qbo_time_activities,
)
from finance.timekeeping import demo_shifts


class TestQuickBooksPayrollPreparation(unittest.TestCase):
    def test_disallow_invalid_realm(self):
        with self.assertRaises(ValueError):
            QBOReadOnlyClient("../../other", "test-token")

    def test_disallow_missing_token(self):
        with self.assertRaises(ValueError):
            QBOReadOnlyClient("1234", "")

    def test_block_write_entities(self):
        client = QBOReadOnlyClient("1234", "test-token")
        with self.assertRaises(ValueError):
            client._query("Paycheck")

    def test_summary_has_no_approval(self):
        entries = [{"Id": "1", "EmployeeRef": {"value": "42"}, "TxnDate": "2026-11-17", "Hours": 8, "Minutes": 30},
                   {"Id": "2", "EmployeeRef": {"value": "42"}, "TxnDate": "2026-11-17", "Hours": 1, "Minutes": 0}]
        result = summarize_qbo_time_activities(entries)
        self.assertEqual(result["daily_hours"][0]["recorded_hours"], "9.5000")
        self.assertFalse(result["daily_hours"][0]["payroll_approved"])

    def test_missing_punch_blocks_payroll(self):
        result = prepare_payroll_review(demo_shifts(), {"JOB-1042", "JOB-1043", "JOB-1044"},
                                        "2026-11-16", "2026-11-22")
        self.assertEqual(result["status"], "REVIEW_ONLY_NOT_SUBMITTED")
        self.assertEqual([r["shift_id"] for r in result["approved_hours_for_review"]], ["SHIFT-005"])
        self.assertTrue(any(x["rule"] == "invalid_shift" for x in result["exceptions"]))


if __name__ == "__main__":
    unittest.main()
