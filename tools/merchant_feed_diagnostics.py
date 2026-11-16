"""Merchant product-feed diagnostics: offline audits and approval-controlled local fixes.

No merchant account writes. Python 3.10+ standard library.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlparse

NS = "http://base.google.com/ns/1.0"
REQUIRED = ("id", "title", "description", "link", "image_link", "availability", "price")
EDITABLE = frozenset({"title", "description", "link", "image_link", "brand", "gtin", "mpn"})
ALLOWED_STOCK = {"in_stock", "out_of_stock", "preorder", "backorder"}
PRIORITY = {"critical": 0, "high": 1, "medium": 2, "low": 3}
HEADERS = ("id", "title", "description", "link", "image_link", "availability",
           "price", "condition", "brand", "gtin", "mpn", "item_group_id")


def fingerprint(item: dict) -> str:
    payload = json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_tsv(path: str) -> list[dict]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if not reader.fieldnames or not set(REQUIRED).issubset(reader.fieldnames):
            raise ValueError("Feed TSV missing required columns")
        if None in reader.fieldnames:
            raise ValueError("Feed TSV contains invalid blank header")
        records = []
        for line, record in enumerate(reader, 2):
            if None in record:
                raise ValueError(f"Malformed TSV row {line}")
            records.append({k: (v or "").strip() for k, v in record.items()})
        return records


def load_rss(path: str) -> list[dict]:
    root = ET.parse(path).getroot()
    if root.tag != "rss":
        raise ValueError("Expected RSS 2.0 document")
    rows = []
    for element in root.findall("./channel/item"):
        item = {}
        for child in element:
            name = child.tag.split("}")[-1]
            if name in item:
                raise ValueError(f"Duplicate RSS field {name}")
            item[name] = (child.text or "").strip()
        rows.append(item)
    return rows


def load_feed(path: str, fmt: str) -> list[dict]:
    if fmt == "auto":
        fmt = "rss" if Path(path).suffix.lower() in (".rss", ".xml") else "tsv"
    return load_rss(path) if fmt == "rss" else load_tsv(path)


def issue(offer_id: str, code: str, priority: str, message: str,
          field: str = "", source: str = "offline", countries=None) -> dict:
    return {
        "offer_id": offer_id, "code": code, "priority": priority,
        "field": field, "message": message, "source": source,
        "countries": countries or [],
        "requires_review": True,
    }


def check_gtin(value: str) -> bool:
    digits = re.sub(r"[\s-]", "", value)
    if len(digits) not in (8, 12, 13, 14) or not digits.isdigit():
        return False
    total = sum(int(d) * (3 if i % 2 else 1)
                for i, d in enumerate(reversed(digits[:-1])))
    return (10 - total % 10) % 10 == int(digits[-1])


def audit(items: list[dict]) -> dict:
    findings = []
    ids = Counter(str(item.get("id") or "").strip() for item in items)
    for number, item in enumerate(items, 1):
        identifier = (item.get("id") or "").strip()
        label = identifier or f"[missing ID at row {number}]"
        if not identifier:
            findings.append(issue(label, "missing_id", "critical", "Missing stable product ID", "id"))
        if identifier and ids[identifier] > 1:
            findings.append(issue(label, "duplicate_id", "critical", "Duplicate product ID", "id"))
        for field in ("title", "description"):
            value = str(item.get(field) or "").strip()
            if not value:
                findings.append(issue(label, "missing_" + field, "high", f"Missing {field}", field))
            elif len(value) > (150 if field == "title" else 5000):
                findings.append(issue(label, "long_" + field, "medium", f"{field} exceeds recommended feed length", field))
        for field in ("link", "image_link"):
            address = str(item.get(field) or "").strip()
            parsed = urlparse(address)
            if parsed.scheme != "https" or not parsed.hostname:
                findings.append(issue(label, "invalid_" + field, "high", f"Missing or invalid HTTPS {field}", field))
        raw_price = (item.get("price") or "").strip()
        match = re.fullmatch(r"(\d+(?:\.\d{1,2})?) ([A-Z]{3})", raw_price)
        if not match:
            findings.append(issue(label, "invalid_price", "critical", "Invalid price/currency format", "price"))
        else:
            try:
                if Decimal(match.group(1)) <= 0:
                    findings.append(issue(label, "invalid_price", "critical", "Price must be positive", "price"))
            except InvalidOperation:
                findings.append(issue(label, "invalid_price", "critical", "Invalid decimal price", "price"))
        if (item.get("availability") or "").strip() not in ALLOWED_STOCK:
            findings.append(issue(label, "invalid_availability", "critical", "Unknown stock status", "availability"))
        gtin = (item.get("gtin") or "").strip()
        if gtin and not check_gtin(gtin):
            findings.append(issue(label, "invalid_gtin", "high", "GTIN checksum or format invalid; verify against manufacturer", "gtin"))
        if not (item.get("brand") or "").strip() and not gtin and not (item.get("mpn") or "").strip():
            findings.append(issue(label, "missing_identifiers", "medium", "No brand, GTIN, or MPN; review product identifier rules"))
    findings.sort(key=lambda x: (PRIORITY[x["priority"]], x["offer_id"], x["code"]))
    return {"items_checked": len(items), "issues": findings,
            "counts": dict(Counter(x["priority"] for x in findings))}


MERCHANT_PRIORITY = {"DISAPPROVED": "critical", "DEMOTED": "high", "WARNING": "medium",
                     "ERROR": "high", "CRITICAL": "critical", "INFO": "low"}


def normalize_merchant_products(payload: dict) -> dict:
    """Normalize Merchant API products.list response with productStatus.itemLevelIssues."""
    if not isinstance(payload, dict) or not isinstance(payload.get("products"), list):
        raise ValueError("Expected Merchant API JSON with products array")
    issues = []
    disapproved = 0
    for product in payload["products"]:
        status = product.get("productStatus") or {}
        product_id = str(product.get("offerId") or product.get("name") or "[unknown]")
        statuses = status.get("destinationStatuses") or []
        if any(row.get("disapprovedCountries") for row in statuses):
            disapproved += 1
        for row in status.get("itemLevelIssues") or []:
            severity = str(row.get("severity") or "WARNING").upper()
            issues.append(issue(
                product_id, str(row.get("code") or "merchant_issue"),
                MERCHANT_PRIORITY.get(severity, "medium"),
                str(row.get("description") or row.get("detail") or "Merchant Center issue"),
                str(row.get("attribute") or ""), "merchant_api",
                row.get("applicableCountries") or [],
            ))
    issues.sort(key=lambda x: (PRIORITY[x["priority"]], x["offer_id"], x["code"]))
    return {"products_checked": len(payload["products"]),
            "disapproved_products": disapproved, "issues": issues,
            "counts": dict(Counter(x["priority"] for x in issues))}


def combine(offline: dict, merchant: dict | None = None) -> dict:
    issues = offline["issues"] + (merchant["issues"] if merchant else [])
    issues.sort(key=lambda x: (PRIORITY[x["priority"]], x["offer_id"], x["code"]))
    return {
        "feed_products": offline["items_checked"],
        "merchant_products": merchant["products_checked"] if merchant else None,
        "merchant_disapproved_products": merchant["disapproved_products"] if merchant else None,
        "issues": issues,
        "issue_counts": dict(Counter(x["priority"] for x in issues)),
        "actions": [
            {
                "offer_id": item["offer_id"],
                "source": item["source"],
                "priority": item["priority"],
                "issue": item["code"],
                "recommendation": recommendation(item),
                "status": "needs_review",
            } for item in issues
        ],
        "read_only": True,
    }


def recommendation(item: dict) -> str:
    attr = item["field"]
    if attr in ("price", "availability"):
        return "Verify storefront and source-of-truth values; do not auto-correct commercial data."
    if attr == "gtin":
        return "Verify manufacturer-issued GTIN; never fabricate identifiers."
    if attr in ("link", "image_link"):
        return "Verify a working, public HTTPS URL for the exact offer."
    if attr in ("title", "description"):
        return "Draft accurate copy from verified product facts for merchant review."
    return "Review Merchant Center documentation and verify authoritative product attributes."


def draft_manifest(items: list[dict], changes: dict[str, dict]) -> list[dict]:
    """Make manifest from explicitly supplied suggestions; no automated AI claims."""
    by_id = {item.get("id"): item for item in items}
    if len(by_id) != len(items) or not all(by_id):
        raise ValueError("Cannot draft fixes for feeds with missing/duplicate IDs")
    manifest = []
    for identifier, patch in changes.items():
        if identifier not in by_id:
            raise ValueError(f"Unknown feed ID {identifier}")
        validate_patch(patch)
        manifest.append({"id": identifier, "expected_sha256": fingerprint(by_id[identifier]),
                         "changes": patch, "approved": False})
    return manifest


def validate_patch(patch: dict) -> None:
    if not isinstance(patch, dict) or not patch or set(patch) - EDITABLE:
        raise ValueError(f"Only {sorted(EDITABLE)} are allowed in patches")
    if any(not isinstance(value, str) or not value.strip() for value in patch.values()):
        raise ValueError("Patches must contain nonempty strings")


def apply_approved(items: list[dict], manifest: list[dict]) -> list[dict]:
    """Create a new local feed; never write Shopify or Google Merchant Center."""
    if not isinstance(manifest, list) or not manifest:
        raise ValueError("Approval manifest must be nonempty")
    by_id = {item.get("id"): item for item in items}
    if len(by_id) != len(items) or not all(by_id):
        raise ValueError("Feed IDs must be present and unique")
    approved_ids = set()
    for entry in manifest:
        if not isinstance(entry, dict) or set(entry) != {"id", "expected_sha256", "changes", "approved"}:
            raise ValueError("Unexpected manifest entry fields")
        identifier = entry["id"]
        if not isinstance(identifier, str) or identifier not in by_id or identifier in approved_ids:
            raise ValueError("Unknown or duplicate approved ID")
        approved_ids.add(identifier)
        if entry["approved"] is not True:
            raise ValueError(f"Entry {identifier} lacks explicit approval")
        if fingerprint(by_id[identifier]) != entry["expected_sha256"]:
            raise ValueError(f"Feed changed since approval: {identifier}")
        validate_patch(entry["changes"])
    result = [dict(row) for row in items]
    amendments = {x["id"]: x["changes"] for x in manifest}
    for row in result:
        if row["id"] in amendments:
            row.update(amendments[row["id"]])
    return result


def write_feed_tsv(path: str, items: list[dict]) -> None:
    fields = list(dict.fromkeys((*HEADERS, *(k for row in items for k in row))))
    with Path(path).open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(items)


def write_feed_rss(path: str, items: list[dict]) -> None:
    ET.register_namespace("g", NS)
    root = ET.Element("rss", version="2.0")
    channel = ET.SubElement(root, "channel")
    ET.SubElement(channel, "title").text = "Reviewed Merchant Feed"
    ET.SubElement(channel, "link").text = "https://example.invalid"
    ET.SubElement(channel, "description").text = "Review-only product feed"
    for row in items:
        element = ET.SubElement(channel, "item")
        for key, value in row.items():
            if value:
                tag = key if key in ("title", "description", "link") else f"{{{NS}}}{key}"
                ET.SubElement(element, tag).text = value
    with Path(path).open("xb") as stream:
        ET.ElementTree(root).write(stream, encoding="utf-8", xml_declaration=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("audit", "draft", "apply"))
    parser.add_argument("--feed", required=True)
    parser.add_argument("--format", choices=("auto", "tsv", "rss"), default="auto")
    parser.add_argument("--merchant-json", help="Optional Merchant API products snapshot")
    parser.add_argument("--changes", help="JSON object {offer_id: {field: new_value}} for draft")
    parser.add_argument("--manifest", help="Approved JSON manifest for apply")
    parser.add_argument("--output", required=True)
    parser.add_argument("--confirm", action="store_true", help="Required for applying locally")
    args = parser.parse_args()
    if Path(args.output).exists():
        parser.error("Refusing to overwrite output")
    items = load_feed(args.feed, args.format)
    if args.command == "audit":
        data = json.loads(Path(args.merchant_json).read_text()) if args.merchant_json else None
        merchant = normalize_merchant_products(data) if data is not None else None
        result = combine(audit(items), merchant)
        Path(args.output).write_text(json.dumps(result, indent=2) + "\n")
    elif args.command == "draft":
        if not args.changes:
            parser.error("draft requires --changes")
        changes = json.loads(Path(args.changes).read_text())
        if not isinstance(changes, dict):
            parser.error("changes must be a JSON object")
        result = draft_manifest(items, changes)
        Path(args.output).write_text(json.dumps(result, indent=2) + "\n")
    else:
        if not args.confirm or not args.manifest:
            parser.error("apply requires --manifest and --confirm")
        manifest = json.loads(Path(args.manifest).read_text())
        updated = apply_approved(items, manifest)
        if args.format == "rss" or (args.format == "auto" and Path(args.feed).suffix.lower() in (".rss", ".xml")):
            write_feed_rss(args.output, updated)
        else:
            write_feed_tsv(args.output, updated)
    print(json.dumps({"command": args.command, "output": args.output, "products": len(items)}))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, ET.ParseError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
