import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.shopify_return_processing import propose, write_new_private

ROOT = Path(__file__).resolve().parents[1]
CASE = json.loads((ROOT / "examples/return_case_sample.json").read_text())
POLICY = json.loads((ROOT / "examples/return_policy_sample.json").read_text())


class ReturnProcessingTests(unittest.TestCase):
    def test_valid_case_is_only_a_proposal(self):
        result = propose(CASE, POLICY)
        self.assertEqual(result["assessment"], "appears_within_stated_policy")
        for key in ("approved", "return_submitted", "refund_issued", "customer_notified"):
            self.assertFalse(result[key])
        self.assertTrue(result["human_review_required"])
        self.assertEqual(len(result["review_sha256"]), 64)

    def test_out_of_window(self):
        c = copy.deepcopy(CASE)
        c["requested_on"] = "2027-01-01"
        result = propose(c, POLICY)
        self.assertEqual(result["assessment"], "manual_review_required")
        self.assertTrue(result["findings"])

    def test_missing_date_needs_review(self):
        c = copy.deepcopy(CASE)
        c["delivered_on"] = None
        self.assertEqual(propose(c, POLICY)["assessment"], "manual_review_required")

    def test_excluded_item_needs_review(self):
        c = copy.deepcopy(CASE)
        c["items"][0]["tags"].append("custom-made")
        self.assertEqual(propose(c, POLICY)["assessment"], "manual_review_required")

    def test_opened_item_needs_review(self):
        c = copy.deepcopy(CASE)
        c["items"][0]["unopened"] = False
        self.assertEqual(propose(c, POLICY)["assessment"], "manual_review_required")

    def test_invalid_quantities_rejected(self):
        c = copy.deepcopy(CASE)
        c["items"][0]["quantity"] = 2
        with self.assertRaises(ValueError):
            propose(c, POLICY)

    def test_duplicate_line_ids_rejected(self):
        c = copy.deepcopy(CASE)
        c["items"].append(copy.deepcopy(c["items"][0]))
        with self.assertRaises(ValueError):
            propose(c, POLICY)

    def test_review_changes_when_case_changes(self):
        c = copy.deepcopy(CASE)
        c["customer_reason"] = "Different reason"
        self.assertNotEqual(propose(c, POLICY)["review_sha256"], propose(CASE, POLICY)["review_sha256"])

    def test_private_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            output = str(Path(d) / "review.json")
            write_new_private(output, propose(CASE, POLICY))
            self.assertEqual(Path(output).stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                write_new_private(output, propose(CASE, POLICY))

if __name__ == "__main__":
    unittest.main()
