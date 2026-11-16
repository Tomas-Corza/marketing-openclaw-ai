"""Presentation-independent adapters to existing Shopify and Merchant tools. No live writes."""
from __future__ import annotations
import csv
import hashlib
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from tools.shopify_bulk_feed import analyze_feed
from tools.merchant_feed_diagnostics import apply_approved, audit, combine, draft_manifest, normalize_merchant_products, validate_patch

MAX_UPLOAD_BYTES = 5_000_000
MAX_PRODUCTS = 5_000
EDITABLE_FIELDS = ("title", "description", "link", "image_link", "brand", "gtin", "mpn")

def ensure_size(data: bytes) -> None:
    if not data or len(data) > MAX_UPLOAD_BYTES:
        raise ValueError("Upload must contain data and be no larger than 5 MB")

def parse_catalog(data: bytes) -> dict:
    ensure_size(data)
    with TemporaryDirectory() as temp:
        source = Path(temp) / "catalog.csv"
        source.write_bytes(data)
        result = analyze_feed(str(source))
    if result["products_scanned"] > MAX_PRODUCTS:
        raise ValueError("Too many products (maximum 5,000)")
    return result

def parse_feed(data: bytes, name: str) -> list[dict]:
    ensure_size(data)
    from tools.merchant_feed_diagnostics import load_feed
    suffix = ".xml" if name.lower().endswith((".xml", ".rss")) else ".tsv"
    with TemporaryDirectory() as temp:
        path = Path(temp) / ("feed" + suffix)
        path.write_bytes(data)
        items = load_feed(str(path), "auto")
    if len(items) > MAX_PRODUCTS:
        raise ValueError("Too many feed items (maximum 5,000)")
    return items

def read_optional_json(data: bytes | None, expected: str) -> dict | None:
    if data is None:
        return None
    ensure_size(data)
    parsed = json.loads(data.decode("utf-8-sig"))
    if not isinstance(parsed, dict) or not isinstance(parsed.get(expected), list):
        raise ValueError(f"Expected JSON object with a '{expected}' array")
    return parsed

def run_diagnostics(items: list[dict], merchant_status: dict | None = None) -> dict:
    merchant = normalize_merchant_products(merchant_status) if merchant_status else None
    return combine(audit(items), merchant)

def source_fingerprint(*parts: bytes) -> str:
    sha = hashlib.sha256()
    for part in parts:
        sha.update(len(part).to_bytes(8, "big"))
        sha.update(part)
    return sha.hexdigest()

def queue_change(items: list[dict], changes: dict, offer_id: str, field: str, new_value: str) -> dict:
    if field not in EDITABLE_FIELDS:
        raise ValueError(f"Field '{field}' is not editable in the dashboard")
    if offer_id not in {item.get("id") for item in items}:
        raise ValueError("Select a valid existing feed product ID")
    proposal = dict(changes.get(offer_id, {}))
    proposal[field] = new_value.strip()
    validate_patch(proposal)
    updated = {key: dict(patch) for key, patch in changes.items()}
    updated[offer_id] = proposal
    draft_manifest(items, updated)
    return updated

def approval_manifest(items: list[dict], changes: dict, approved_ids: set[str]) -> list[dict]:
    manifest = draft_manifest(items, changes) if changes else []
    for entry in manifest:
        entry["approved"] = entry["id"] in approved_ids
    return manifest

def locally_reviewed_preview(items: list[dict], manifest: list[dict]) -> list[dict]:
    if not manifest:
        raise ValueError("No changes queued")
    return apply_approved(items, manifest)

def tsv_bytes(items: list[dict]) -> bytes:
    if not items:
        raise ValueError("No feed records")
    fields = list(dict.fromkeys(key for item in items for key in item))
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields, delimiter="\t")
    writer.writeheader()
    writer.writerows(items)
    return output.getvalue().encode("utf-8")

def json_bytes(payload) -> bytes:
    return (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8")

def summarize(catalog: dict, diagnostic: dict, ai_report: dict | None) -> dict:
    return {
        "catalog_products": catalog["products_scanned"],
        "feed_products": diagnostic["feed_products"],
        "feed_issues": len(diagnostic["issues"]),
        "critical_issues": diagnostic["issue_counts"].get("critical", 0),
        "catalog_findings": sum(catalog["finding_counts"].values()),
        "ai_drafts": len([x for x in (ai_report or {}).get("items", []) if "suggested_changes" in x]),
    }
