"""Explicit, review-first Gmail message -> customer-inquiry draft integration.

Requires a merchant-authorized OAuth access token in GMAIL_ACCESS_TOKEN. Only
reads one supplied message ID and creates a Gmail DRAFT after fingerprint approval.
No Gmail messages.send / drafts.send / unattended polling / automatic replies.
"""
from __future__ import annotations

import argparse
import base64
from email.message import EmailMessage
from email.utils import parseaddr
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

from tools.customer_inquiry_assistant import load_json, make_draft, validated_knowledge

GMAIL_ROOT = "https://gmail.googleapis.com/gmail/v1/users/me"
GMAIL_ID = re.compile(r"^[A-Za-z0-9_-]{4,120}$")
MESSAGE_ID = re.compile(r"^<[^<>\r\n\s]+@[^<>\r\n\s]+>$")
ADDRESS = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_\x60{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def google_request(method: str, path: str, token: str, payload: dict | None = None) -> dict:
    if not token or "\r" in token or "\n" in token:
        raise ValueError("An authorized GMAIL_ACCESS_TOKEN is required")
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        GMAIL_ROOT + path, data=data, method=method,
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Gmail API HTTP {exc.code}; confirm authorization and scopes") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError("Gmail API connection failed") from exc


def header_value(payload: dict, name: str) -> str:
    headers = payload.get("headers") or []
    for header in headers:
        if str(header.get("name", "")).lower() == name.lower():
            return str(header.get("value") or "")
    return ""


def _decode_body(part: dict) -> str:
    mime = part.get("mimeType")
    if mime == "text/plain":
        raw = (part.get("body") or {}).get("data")
        if isinstance(raw, str):
            try:
                decoded = base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4))
                return decoded.decode("utf-8", errors="replace")
            except (ValueError, UnicodeError) as exc:
                raise ValueError("Invalid message body encoding") from exc
    for child in part.get("parts") or []:
        value = _decode_body(child)
        if value:
            return value
    return ""


def parse_message(message: dict, expected_id: str) -> dict:
    if not isinstance(message, dict) or message.get("id") != expected_id:
        raise ValueError("Received a different Gmail message than requested")
    payload = message.get("payload")
    if not isinstance(payload, dict):
        raise ValueError("Gmail response lacked message payload")
    if header_value(payload, "Auto-Submitted").lower().strip() not in ("", "no"):
        raise ValueError("Refusing an automatically generated email")
    if header_value(payload, "List-Id") or header_value(payload, "List-Unsubscribe"):
        raise ValueError("Refusing mailing-list messages")
    sender = parseaddr(header_value(payload, "From"))[1]
    if not ADDRESS.fullmatch(sender) or "\r" in sender or "\n" in sender:
        raise ValueError("Sender address is not a valid single mailbox")
    subject = header_value(payload, "Subject").strip()
    if not subject or len(subject) > 300 or any(c in subject for c in "\r\n"):
        raise ValueError("Invalid subject")
    references = header_value(payload, "References").strip()
    msgid = header_value(payload, "Message-ID").strip()
    if not MESSAGE_ID.fullmatch(msgid):
        raise ValueError("Missing or invalid Message-ID required to thread the reply")
    if references:
        for item in references.split():
            if not MESSAGE_ID.fullmatch(item):
                raise ValueError("Invalid References header")
    thread_id = message.get("threadId")
    if not isinstance(thread_id, str) or not GMAIL_ID.fullmatch(thread_id):
        raise ValueError("Invalid Gmail thread ID")
    labels = message.get("labelIds") or []
    if any(x in labels for x in ("SENT", "DRAFT", "TRASH", "SPAM")):
        raise ValueError("Refusing sent, draft, trash or spam messages")
    body = _decode_body(payload).strip()
    if not body or len(body) > 8000:
        raise ValueError("Email must contain 1-8,000 characters of plain text; HTML-only mail is not supported")
    return {
        "sender": sender, "subject": subject, "body": body,
        "message_id": msgid, "references": references, "thread_id": thread_id,
        "gmail_message_id": expected_id,
    }


def get_inquiry(gmail_message_id: str, token: str) -> dict:
    if not GMAIL_ID.fullmatch(gmail_message_id):
        raise ValueError("Invalid Gmail message identifier")
    message = google_request("GET", "/messages/" + urllib.parse.quote(gmail_message_id) + "?format=full", token)
    return parse_message(message, gmail_message_id)


def create_preview(message: dict, knowledge: dict, *, ai: bool = False, model: str = "gpt-4.1-mini",
                   api_key: str = "") -> dict:
    inquiry = {"id": message["gmail_message_id"], "subject": message["subject"], "message": message["body"]}
    generated = make_draft(inquiry, validated_knowledge(knowledge), ai=ai, model=model, api_key=api_key)
    draft = generated["draft"]
    if generated["escalate_to_human"]:
        raise ValueError("Sensitive inquiry requires manual handling; no Gmail draft created")
    if not isinstance(draft["body"], str) or not draft["body"].strip():
        raise ValueError("Draft is empty")
    reply_to = message["sender"]
    subject = message["subject"] if message["subject"].lower().startswith("re:") else "Re: " + message["subject"]
    proposal = {
        "recipient": reply_to, "subject": subject, "body": draft["body"],
        "thread_id": message["thread_id"], "in_reply_to": message["message_id"],
        "references": (message["references"] + " " + message["message_id"]).strip(),
        "source_message_id": message["gmail_message_id"], "source_body_sha256": hashlib.sha256(message["body"].encode()).hexdigest(),
    }
    digest = hashlib.sha256(json.dumps(proposal, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return {
        "source_message_id": message["gmail_message_id"],
        "category": generated["category"], "evidence_ids": generated["evidence_ids"],
        "reply": proposal, "approval_sha256": digest, "approved": False,
        "sent": False, "gmail_draft_created": False,
        "review_notes": generated["review_notes"],
        "missing_information": draft["missing_information"],
    }


def create_gmail_draft(preview: dict, approval_sha256: str, confirmed: bool, token: str) -> dict:
    proposal = preview["reply"]
    expected = hashlib.sha256(json.dumps(proposal, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    if not confirmed or not re.fullmatch(r"[a-f0-9]{64}", approval_sha256 or "") or expected != approval_sha256:
        raise ValueError("Explicit confirmation and the exact reviewed reply hash are required")
    if preview.get("approval_sha256") != expected or preview.get("sent") is not False:
        raise ValueError("Invalid or altered preview")
    if proposal["source_message_id"] != preview["source_message_id"]:
        raise ValueError("Source message mismatch")
    email = EmailMessage()
    email["To"] = proposal["recipient"]
    email["Subject"] = proposal["subject"]
    email["In-Reply-To"] = proposal["in_reply_to"]
    email["References"] = proposal["references"]
    email.set_content(proposal["body"])
    raw = base64.urlsafe_b64encode(email.as_bytes()).decode("ascii")
    result = google_request("POST", "/drafts", token, {"message": {"raw": raw, "threadId": proposal["thread_id"]}})
    if not isinstance(result, dict) or not result.get("id"):
        raise RuntimeError("Gmail draft response was incomplete; inspect Drafts before retrying")
    return {"gmail_draft_created": True, "draft_id": result["id"],
            "source_message_id": preview["source_message_id"], "sent": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preview", "create"))
    parser.add_argument("--message-id", required=True, help="Explicit authorized Gmail message ID")
    parser.add_argument("--knowledge", required=True, help="Approved product/policy knowledge JSON")
    parser.add_argument("--approve-sha256", help="Exact hash printed by preview")
    parser.add_argument("--confirm", action="store_true", help="Merchant approved this exact draft")
    parser.add_argument("--ai", action="store_true", help="Optional OpenAI generated draft")
    parser.add_argument("--allow-external-data", action="store_true", help="Explicit authorization to share email text with OpenAI")
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"))
    args = parser.parse_args()
    if args.ai and not args.allow_external_data:
        parser.error("--ai requires --allow-external-data and explicit permission")
    token = os.getenv("GMAIL_ACCESS_TOKEN", "")
    if not token:
        parser.error("GMAIL_ACCESS_TOKEN must be set for this authorized Gmail mailbox")
    source = get_inquiry(args.message_id, token)
    preview = create_preview(source, load_json(args.knowledge), ai=args.ai,
                             model=args.model, api_key=os.getenv("OPENAI_API_KEY", ""))
    if args.command == "preview":
        # Preview includes the proposed reply; handle this private console output securely.
        print(json.dumps(preview, indent=2, ensure_ascii=False))
    else:
        result = create_gmail_draft(preview, args.approve_sha256 or "", args.confirm, token)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
