import base64
import unittest
from tools.gmail_approved_send import approved_send, sha256, validate

MESSAGE = {"to": "recipient@example.com", "subject": "Hello", "body": "Test body"}


class ApprovedSendTests(unittest.TestCase):
    def test_hash_deterministic(self):
        self.assertEqual(sha256(MESSAGE), sha256({"body": "Test body", "subject": "Hello", "to": "recipient@example.com"}))

    def test_refuses_header_injection(self):
        for field in ("to", "subject"):
            bad = dict(MESSAGE)
            bad[field] += "\nBcc: intruder@example.com"
            with self.assertRaises(ValueError):
                validate(bad)

    def test_no_send_without_approval(self):
        def fail(*args):
            self.fail("Unexpected transport call")
        for digest, approved, token in [(sha256(MESSAGE), False, "token"), ("0" * 64, True, "token"), (sha256(MESSAGE), True, "")]:
            with self.assertRaises(ValueError):
                approved_send(MESSAGE, digest, approved, token, fail)

    def test_approved_send(self):
        def fake(token, raw):
            self.assertEqual(token, "token")
            content = base64.urlsafe_b64decode(raw).decode()
            self.assertIn("To: recipient@example.com", content)
            self.assertNotIn("Bcc:", content)
            return {"id": "fake-id"}
        self.assertEqual(approved_send(MESSAGE, sha256(MESSAGE), True, "token", fake)["gmail_message_id"], "fake-id")


if __name__ == "__main__":
    unittest.main()
