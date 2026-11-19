"""Single-message Gmail send: preview locally, require exact-content approval."""
import argparse
import base64
from email.message import EmailMessage
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request

EMAIL = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_\x60{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
SHA = re.compile(r"^[a-f0-9]{64}$")
API = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"


def validate(message):
    if not isinstance(message, dict) or set(message) != {"to", "subject", "body"}:
        raise ValueError("Expected exactly to, subject, body")
    to, subject, body = message["to"], message["subject"], message["body"]
    if not isinstance(to, str) or len(to) > 254 or not EMAIL.fullmatch(to):
        raise ValueError("A single valid recipient email is required")
    if not isinstance(subject, str) or not 1 <= len(subject.strip()) <= 250 or any(c in subject for c in "\r\n"):
        raise ValueError("Invalid subject")
    if not isinstance(body, str) or not 1 <= len(body.strip()) <= 50000 or "\x00" in body:
        raise ValueError("Invalid plain-text body")
    return {"to": to, "subject": subject, "body": body}


def sha256(message):
    normalized = validate(message)
    value = json.dumps(normalized, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def gmail_send(token, raw):
    request = urllib.request.Request(
        API, data=json.dumps({"raw": raw}).encode("utf-8"), method="POST",
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Gmail HTTP {exc.code}; check Sent folder before retrying") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError("Gmail connection failed; check Sent folder before retrying") from exc


def approved_send(message, approved_hash, confirm, token, transport=None):
    message = validate(message)
    if not confirm or not SHA.fullmatch(approved_hash or "") or sha256(message) != approved_hash:
        raise ValueError("Explicit approval and matching preview SHA-256 required")
    if not token or any(x in token for x in "\r\n"):
        raise ValueError("GMAIL_ACCESS_TOKEN is required from an authorized Gmail OAuth connection")
    mail = EmailMessage()
    mail["To"] = message["to"]
    mail["Subject"] = message["subject"]
    mail.set_content(message["body"])
    raw = base64.urlsafe_b64encode(mail.as_bytes()).decode("ascii")
    result = (transport or gmail_send)(token, raw)
    if not isinstance(result, dict) or not isinstance(result.get("id"), str):
        raise RuntimeError("Outcome unknown; check Gmail Sent before retrying")
    return {"sent": True, "gmail_message_id": result["id"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preview", "send"))
    parser.add_argument("--message", required=True, help="Private JSON with to, subject, body")
    parser.add_argument("--approve-sha256")
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args()
    message = validate(json.loads(Path(args.message).read_text(encoding="utf-8")))
    if args.command == "preview":
        print(json.dumps({"message": message, "approval_sha256": sha256(message), "sent": False},
                         ensure_ascii=False, indent=2))
    else:
        print(json.dumps(approved_send(message, args.approve_sha256, args.confirm,
                                       os.getenv("GMAIL_ACCESS_TOKEN", "")), indent=2))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print("Error: " + str(exc), file=sys.stderr)
        sys.exit(1)
