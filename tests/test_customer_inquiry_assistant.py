"""Offline tests for review-only customer inquiry workflow."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tools.customer_inquiry_assistant import (
    classify, make_draft, private_output, select_evidence, validated_inquiry, validated_knowledge,
    ai_draft,
)

KNOWLEDGE = {
    "products": [{
        "id": "fixture-001", "name": "Example Pendant",
        "facts": {"Finish": "Matte black", "Voltage": "120V"},
        "url": "https://example.com/products/example-pendant",
    }],
    "policies": [{
        "id": "support-return", "category": "returns",
        "text": "Our team reviews return eligibility based on the order details.",
    }],
}
INQUIRY = {"id": "demo-001", "subject": "Example Pendant specifications",
           "message": "What voltage does the Example Pendant use?"}


class InquiryAssistantTests(unittest.TestCase):
    def test_product_inquiry_is_grounded_and_unsent(self):
        result = make_draft(INQUIRY, KNOWLEDGE)
        self.assertEqual(result["category"], "product_question")
        self.assertEqual(result["evidence_ids"], ["product:fixture-001"])
        self.assertIn("120V", result["draft"]["body"])
        self.assertTrue(result["draft"]["subject"].startswith("Re: "))
        self.assertFalse(result["sent"])
        self.assertFalse(result["approved"])
        self.assertEqual(result["approval_status"], "pending")

    def test_no_matching_product_asks_for_details(self):
        result = make_draft({"id": "a", "subject": "Dimensions",
                             "message": "What are the dimensions?"}, KNOWLEDGE)
        self.assertEqual(result["category"], "product_question")
        self.assertNotIn("120V", result["draft"]["body"])
        self.assertTrue(result["draft"]["missing_information"])

    def test_order_status_never_guesses_tracking(self):
        result = make_draft({"id": "order", "subject": "Where is my order?",
                             "message": "Can you check delivery?"}, KNOWLEDGE)
        self.assertEqual(result["category"], "order_status")
        self.assertIn("order number", result["draft"]["body"])
        self.assertNotIn("delivered", result["draft"]["body"])

    def test_sensitive_inquiry_is_flagged(self):
        result = make_draft({"id": "urgent", "subject": "Electrical fire",
                             "message": "An electrical fire occurred."}, KNOWLEDGE)
        self.assertTrue(result["escalate_to_human"])
        self.assertFalse(result["sent"])

    def test_returns_use_only_approved_policy(self):
        result = make_draft({"id": "r", "subject": "Return",
                             "message": "I'd like to return my order."}, KNOWLEDGE)
        self.assertIn("Our team reviews return eligibility", result["draft"]["body"])
        self.assertEqual(result["evidence_ids"], ["policy:support-return"])

    def test_bad_inputs_rejected(self):
        for invalid in ({"id": "a", "subject": "", "message": "hello"},
                        {"id": "a/b", "subject": "x", "message": "x"},
                        {"id": "a", "subject": "x", "message": "x", "email": "private@example.com"}):
            with self.assertRaises(ValueError):
                validated_inquiry(invalid)
        with self.assertRaises(ValueError):
            validated_knowledge({"products": [{"id": "p", "name": "x", "facts": {}, "url": "http://bad.test"}], "policies": []})

    def test_private_file_cannot_be_overwritten(self):
        result = make_draft(INQUIRY, KNOWLEDGE)
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "draft.json")
            private_output(path, result)
            self.assertEqual(Path(path).stat().st_mode & 0o777, 0o600)
            self.assertEqual(json.loads(Path(path).read_text())["sent"], False)
            with self.assertRaises(FileExistsError):
                private_output(path, result)

    def test_ai_is_optional_and_requires_key(self):
        with self.assertRaises(ValueError):
            make_draft(INQUIRY, KNOWLEDGE, ai=True, api_key="")

    def test_no_auto_send_even_with_ai(self):
        with patch("tools.customer_inquiry_assistant.ai_draft",
                   return_value={"subject": "Re: Example", "body": "Draft", "missing_information": []}) as model:
            result = make_draft(INQUIRY, KNOWLEDGE, ai=True, api_key="fake-token")
        self.assertFalse(result["sent"])
        self.assertFalse(result["approved"])
        model.assert_called_once()


if __name__ == "__main__":
    unittest.main()
