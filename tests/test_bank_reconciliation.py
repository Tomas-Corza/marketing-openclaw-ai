import unittest
from finance.bank_reconciliation import reconcile, synthetic_example


class TestBankReconciliation(unittest.TestCase):
    def test_synthetic_example(self):
        bank, ledger, mapping = synthetic_example()
        result = reconcile(bank, ledger, mapping)
        self.assertEqual(result["summary"]["proposed_matches"], 2)
        self.assertEqual(result["summary"]["exceptions"], 5)
        self.assertTrue(all(x["requires_approval"] for x in result["proposed_matches"]))

    def test_missing_mapping_does_not_match(self):
        bank, ledger, mapping = synthetic_example()
        self.assertEqual(reconcile(bank[:1], ledger[:1], {})["proposed_matches"], [])

    def test_duplicate_bank_id_is_held(self):
        bank, ledger, mapping = synthetic_example()
        result = reconcile([bank[0], bank[0]], [ledger[0]], mapping)
        self.assertEqual(result["proposed_matches"], [])

    def test_pending_is_held(self):
        bank, ledger, mapping = synthetic_example()
        result = reconcile([bank[2]], [], mapping)
        self.assertEqual(result["proposed_matches"], [])
        self.assertIn("Pending", result["exceptions"][0]["reason"])


if __name__ == "__main__":
    unittest.main()
