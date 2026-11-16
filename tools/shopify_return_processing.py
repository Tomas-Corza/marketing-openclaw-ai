"""Review-only Shopify return case triage.

No Shopify API calls, refunds, return authorizations, labels, or customer messages.
Use merchant-verified JSON and human-approved policies; export review proposals only.
"""
from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import re
import sys

ORDER_GID = re.compile(r"^gid://shopify/Order/[0-9]+$")
LINE_GID = re.compile(r"^gid://shopify/FulfillmentLineItem/[0-9]+$")


def load_json(path: str) -> dict:
    p = Path(path)
    if p.stat().st_size > 100_000:
        raise ValueError("Input exceeds 100 KB")
    obj = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("Input must be a JSON object")
    return obj


def validate_policy(p: dict) -> dict:
    if set(p) != {"name", "window_days", "excluded_tags", "requires_unopened", "exceptions_need_review"}:
        raise ValueError("Policy requires name, window_days, excluded_tags, requires_unopened, exceptions_need_review")
    if not isinstance(p["name"], str) or not p["name"].strip():
        raise ValueError("Policy name is required")
    if type(p["window_days"]) is not int or not 0 <= p["window_days"] <= 365:
        raise ValueError("window_days must be an integer between 0 and 365")
    if type(p["requires_unopened"]) is not bool or type(p["exceptions_need_review"]) is not bool:
        raise ValueError("Policy boolean fields must be true/false")
    if not isinstance(p["excluded_tags"], list) or len(p["excluded_tags"]) > 50 or not all(
        isinstance(x, str) and x.strip() and len(x) <= 80 for x in p["excluded_tags"]
    ):
        raise ValueError("excluded_tags must contain up to 50 strings")
    return p


def validate_case(c: dict) -> dict:
    expected = {"case_id", "order_id", "delivered_on", "requested_on", "customer_reason", "items"}
    if set(c) != expected:
        raise ValueError("Unexpected or missing return-case fields")
    if not isinstance(c["case_id"], str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", c["case_id"]):
        raise ValueError("case_id must be a safe identifier")
    if not isinstance(c["order_id"], str) or not ORDER_GID.fullmatch(c["order_id"]):
        raise ValueError("A valid Shopify order GID is required")
    for key in ("delivered_on", "requested_on"):
        if c[key] is not None:
            if not isinstance(c[key], str):
                raise ValueError(key + " must be a date string or null")
            try:
                date.fromisoformat(c[key])
            except ValueError as exc:
                raise ValueError("Invalid date: " + key) from exc
    if c["delivered_on"] and c["requested_on"] and date.fromisoformat(c["requested_on"]) < date.fromisoformat(c["delivered_on"]):
        raise ValueError("Request date cannot precede delivery")
    if not isinstance(c["customer_reason"], str) or not 0 < len(c["customer_reason"].strip()) <= 2000:
        raise ValueError("Customer reason is required (up to 2,000 characters)")
    if not isinstance(c["items"], list) or not 1 <= len(c["items"]) <= 25:
        raise ValueError("Provide 1-25 items")
    seen = set()
    for i in c["items"]:
        if not isinstance(i, dict) or set(i) != {"fulfillment_line_item_id", "title", "quantity", "fulfilled_quantity", "already_returned_quantity", "tags", "unopened"}:
            raise ValueError("Invalid return item schema")
        gid = i["fulfillment_line_item_id"]
        if not isinstance(gid, str) or not LINE_GID.fullmatch(gid) or gid in seen:
            raise ValueError("Fulfillment line item IDs must be unique valid GIDs")
        seen.add(gid)
        if not isinstance(i["title"], str) or not i["title"].strip() or len(i["title"]) > 300:
            raise ValueError("Product title is required")
        if any(type(i[k]) is not int or i[k] < 0 for k in ("quantity", "fulfilled_quantity", "already_returned_quantity")):
            raise ValueError("Quantities must be nonnegative integers")
        if not 1 <= i["quantity"] <= i["fulfilled_quantity"] - i["already_returned_quantity"]:
            raise ValueError("Requested quantity exceeds available fulfilled, unreturned quantity")
        if not isinstance(i["tags"], list) or not all(isinstance(t, str) for t in i["tags"]):
            raise ValueError("Product tags must be a list")
        if i["unopened"] is not None and type(i["unopened"]) is not bool:
            raise ValueError("unopened must be true, false, or null")
    return c


def propose(c: dict, p: dict) -> dict:
    validate_case(c)
    validate_policy(p)
    findings = []
    if c["delivered_on"] is None or c["requested_on"] is None:
        findings.append("Verify delivery and request dates before assessing the return window")
    else:
        elapsed = (date.fromisoformat(c["requested_on"]) - date.fromisoformat(c["delivered_on"])).days
        if elapsed > p["window_days"]:
            findings.append(f"Request is outside the stated {p['window_days']}-day window; staff must review exceptions and applicable consumer rights")
    excluded = {v.casefold() for v in p["excluded_tags"]}
    for i in c["items"]:
        if excluded.intersection({v.casefold() for v in i["tags"]}):
            findings.append(f"{i['title']}: item has a policy-excluded tag; employee must assess")
        if p["requires_unopened"] and i["unopened"] is not True:
            findings.append(f"{i['title']}: unopened condition not verified")
    result = {
        "case_id": c["case_id"],
        "assessment": "manual_review_required" if findings else "appears_within_stated_policy",
        "findings": findings,
        "request_manifest": {
            "order_id": c["order_id"],
            "items": [{"fulfillment_line_item_id": i["fulfillment_line_item_id"], "quantity": i["quantity"]} for i in c["items"]],
            "customer_reason": c["customer_reason"],
        },
        "customer_response_draft": (
            "Thank you for contacting us about your return. Our team will review the order and "
            "applicable return policy before confirming next steps. No refund or return authorization "
            "has been issued."
        ),
        "approved": False,
        "return_submitted": False,
        "refund_issued": False,
        "customer_notified": False,
        "human_review_required": True,
        "disclaimer": "Policy screening is not a legal eligibility determination. Confirm store records, consumer rights, and the current return state before any action.",
    }
    snapshot = json.dumps({"case": c, "policy": p, "proposal": result}, sort_keys=True, ensure_ascii=False)
    result["review_sha256"] = hashlib.sha256(snapshot.encode("utf-8")).hexdigest()
    return result


def write_new_private(path: str, output: dict) -> None:
    dest = Path(path)
    if dest.is_symlink():
        raise ValueError("Output must not be a symlink")
    fd = os.open(str(dest), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
        f.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, help="Private, verified return-case JSON")
    parser.add_argument("--policy", required=True, help="Merchant-approved policy JSON")
    parser.add_argument("--output", required=True, help="New private review JSON path")
    args = parser.parse_args()
    result = propose(load_json(args.case), load_json(args.policy))
    write_new_private(args.output, result)
    print(json.dumps({"output": args.output, "assessment": result["assessment"], "review_sha256": result["review_sha256"], "submitted": False}))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
