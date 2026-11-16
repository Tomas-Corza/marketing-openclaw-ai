"""Mocked Gmail inquiry -> human-reviewed draft tests. No real account access."""
import base64
from email import message_from_bytes
import unittest
from unittest.mock import patch

from tools.gmail_inquiry_drafts import (
    create_gmail_draft, create_preview, get_inquiry, parse_message
)

KNOWLEDGE = {"products": [{"id":"fixture-001","name":"Example Pendant",
            "facts":{"Voltage":"120V"},"url":"https://example.com/p/pendant"}], "policies":[]}


def gmail_message(body="What voltage does the Example Pendant use?", **overrides):
    encoded=base64.urlsafe_b64encode(body.encode()).decode().rstrip("=")
    message={
      "id":"abcD1234","threadId":"thread1234","labelIds":["INBOX"],
      "payload":{"mimeType":"text/plain","headers":[
        {"name":"From","value":"Demo Buyer <buyer@example.com>"},
        {"name":"Subject","value":"Example Pendant question"},
        {"name":"Message-ID","value":"<example-001@example.com>"}],
        "body":{"data":encoded}}}
    message.update(overrides)
    return message


class GmailDraftTests(unittest.TestCase):
    def test_parse_message_and_thread(self):
        parsed=parse_message(gmail_message(),"abcD1234")
        self.assertEqual(parsed["sender"],"buyer@example.com")
        self.assertEqual(parsed["thread_id"],"thread1234")
        self.assertIn("voltage",parsed["body"])

    def test_preview_does_not_call_gmail(self):
        message=parse_message(gmail_message(),"abcD1234")
        with patch("tools.gmail_inquiry_drafts.google_request") as api:
            result=create_preview(message,KNOWLEDGE)
            api.assert_not_called()
        self.assertEqual(result["category"],"product_question")
        self.assertIn("120V",result["reply"]["body"])
        self.assertEqual(result["reply"]["recipient"],"buyer@example.com")
        self.assertFalse(result["sent"])
        self.assertFalse(result["gmail_draft_created"])
        self.assertFalse(result["approved"])

    def test_draft_creation_requires_matching_approval(self):
        preview=create_preview(parse_message(gmail_message(),"abcD1234"),KNOWLEDGE)
        with patch("tools.gmail_inquiry_drafts.google_request") as api:
            with self.assertRaises(ValueError):
                create_gmail_draft(preview,"invalid",True,"token")
            with self.assertRaises(ValueError):
                create_gmail_draft(preview,preview["approval_sha256"],False,"token")
            api.assert_not_called()

    def test_gmail_draft_is_never_sent(self):
        preview=create_preview(parse_message(gmail_message(),"abcD1234"),KNOWLEDGE)
        with patch("tools.gmail_inquiry_drafts.google_request",return_value={"id":"draft0001"}) as api:
            result=create_gmail_draft(preview,preview["approval_sha256"],True,"token")
            self.assertEqual(result["draft_id"],"draft0001")
            self.assertFalse(result["sent"])
            args=api.call_args.args
            self.assertEqual(args[0],"POST")
            self.assertEqual(args[1],"/drafts")
            self.assertEqual(args[3]["message"]["threadId"],"thread1234")
            raw=base64.urlsafe_b64decode(args[3]["message"]["raw"])
            email=message_from_bytes(raw)
            self.assertEqual(email["To"],"buyer@example.com")
            self.assertEqual(email["In-Reply-To"],"<example-001@example.com>")
            self.assertIn("120V",email.get_payload(decode=True).decode())

    def test_reject_list_and_auto_emails(self):
        for name,value in (("List-Id","mailer.example"),("Auto-Submitted","auto-generated")):
            msg=gmail_message()
            msg["payload"]["headers"].append({"name":name,"value":value})
            with self.subTest(name=name),self.assertRaises(ValueError):
                parse_message(msg,"abcD1234")

    def test_reject_spam_and_html_only(self):
        with self.assertRaises(ValueError):
            parse_message(gmail_message(labelIds=["SPAM"]),"abcD1234")
        msg=gmail_message()
        msg["payload"]["mimeType"]="text/html"
        with self.assertRaises(ValueError):
            parse_message(msg,"abcD1234")

    def test_escalated_inquiry_not_drafted(self):
        msg=parse_message(gmail_message(body="There was an electrical fire involving Example Pendant"),"abcD1234")
        with self.assertRaisesRegex(ValueError,"manual handling"):
            create_preview(msg,KNOWLEDGE)

    def test_fetch_requires_explicit_message_id(self):
        with patch("tools.gmail_inquiry_drafts.google_request",return_value=gmail_message()) as api:
            self.assertEqual(get_inquiry("abcD1234","token")["gmail_message_id"],"abcD1234")
            self.assertEqual(api.call_args.args[0],"GET")
            self.assertIn("format=full",api.call_args.args[1])
        with self.assertRaises(ValueError):
            get_inquiry("../other","token")


if __name__=="__main__":
    unittest.main()
