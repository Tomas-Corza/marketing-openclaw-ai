"""Shopify CSV feed optimizer: offline audit, proposals, and approval-gated API batch apply.

Python standard library only. Never check in real merchant exports or credentials.
Run from the repository root.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

try:
    from tools.shopify_product_pages import (
        PRODUCT_QUERY, UPDATE_MUTATION, audit, load_proposal,
        product_gid, shopify_graphql,
    )
except ModuleNotFoundError:
    from shopify_product_pages import (
        PRODUCT_QUERY, UPDATE_MUTATION, audit, load_proposal,
        product_gid, shopify_graphql,
    )

HEADERS = {"Handle", "Title", "Body (HTML)"}
APPROVAL_FIELDS = {"id", "expected_sha256", "changes", "approved"}


def plain_text(value: str) -> str:
    value = re.sub(r"<[^>]*>", " ", value or "")
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def stable_snapshot(product: dict) -> dict:
    return {
        "title": product.get("title") or "",
        "descriptionHtml": product.get("descriptionHtml") or "",
        "seo": {
            "title": (product.get("seo") or {}).get("title") or "",
            "description": (product.get("seo") or {}).get("description") or "",
        },
    }


def snapshot_hash(product: dict) -> str:
    value = json.dumps(stable_snapshot(product), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_feed(path: str) -> list[dict]:
    """Convert a Shopify product CSV with variant/image rows into unique products."""
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not HEADERS.issubset(reader.fieldnames):
            raise ValueError("Expected Shopify CSV columns: Handle, Title, Body (HTML)")
        unique = {}
        for number, row in enumerate(reader, start=2):
            handle_value = (row.get("Handle") or "").strip()
            if not handle_value:
                continue
            if handle_value not in unique:
                unique[handle_value] = {
                    "handle": handle_value,
                    "title": "",
                    "descriptionHtml": "",
                    "vendor": "",
                    "productType": "",
                    "seo": {"title": "", "description": ""},
                    "source_row": number,
                }
            product = unique[handle_value]
            for source, target in (
                ("Title", "title"), ("Body (HTML)", "descriptionHtml"),
                ("Vendor", "vendor"), ("Type", "productType"),
            ):
                if not product[target] and row.get(source):
                    product[target] = row[source].strip()
            for source, target in (
                ("SEO Title", "title"), ("SEO Description", "description")
            ):
                if not product["seo"][target] and row.get(source):
                    product["seo"][target] = row[source].strip()
        return list(unique.values())


def suggested_content(product: dict) -> dict:
    """Conservative drafts from existing facts only, not fabricated specifications."""
    current_title = product.get("title") or ""
    seo = product.get("seo") or {}
    suggestion = {}
    if current_title and not (seo.get("title") or "").strip():
        vendor = (product.get("vendor") or "").strip()
        suffix = (" | " + vendor) if vendor and vendor.lower() not in current_title.lower() else ""
        suggestion.setdefault("seo", {})["title"] = (current_title + suffix)[:70]
    description = plain_text(product.get("descriptionHtml") or "")
    if description and not (seo.get("description") or "").strip():
        suggestion.setdefault("seo", {})["description"] = description[:155].rstrip()
    return suggestion


def analyze_feed(path: str) -> dict:
    products = load_feed(path)
    report = []
    proposals = []
    counts = Counter()
    for product in products:
        assessment = audit(product)
        for finding in assessment["findings"]:
            counts[finding] += 1
        recommended = suggested_content(product)
        report.append({
            "handle": product["handle"],
            "source_row": product["source_row"],
            "title": product["title"],
            "description_characters": assessment["description_characters"],
            "findings": assessment["findings"],
            "draft_available": bool(recommended),
        })
        if recommended:
            proposals.append({
                "handle": product["handle"],
                "source_row": product["source_row"],
                "suggested_changes": recommended,
                "review_required": True,
            })
    return {
        "source": "Shopify CSV export",
        "products_scanned": len(products),
        "finding_counts": dict(counts),
        "audit": report,
        "drafts": proposals,
        "note": "Drafts are deterministic, not AI-generated, and cannot be applied without separate approved product-ID mappings.",
    }


def write_report(report: dict, output: str) -> None:
    target = Path(output)
    if target.exists():
        raise FileExistsError(f"Refusing to overwrite existing report: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_manifest(path: str) -> list[dict]:
    """An operator-assembled manifest using authoritative Shopify product GIDs."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, list) or not raw:
        raise ValueError("Manifest must be a nonempty list")
    seen = set()
    for index, entry in enumerate(raw):
        if not isinstance(entry, dict) or set(entry) != APPROVAL_FIELDS:
            raise ValueError(f"Manifest entry {index} must have id, expected_sha256, changes, approved")
        gid = product_gid(str(entry["id"]))
        if gid in seen:
            raise ValueError(f"Duplicate product ID: {gid}")
        seen.add(gid)
        if entry["approved"] is not True:
            raise ValueError(f"Product {gid} is not explicitly approved")
        if not re.fullmatch("[a-f0-9]{64}", str(entry["expected_sha256"])):
            raise ValueError(f"Expected SHA256 snapshot hash missing for {gid}")
        # Reuse the allowlist and nested schema validation from the single-product tool.
        changes = entry["changes"]
        if not isinstance(changes, dict) or not changes:
            raise ValueError("changes must be a nonempty object")
        if set(changes) - {"title", "descriptionHtml", "seo"}:
            raise ValueError("Only title, descriptionHtml and seo can be changed")
        if "title" in changes and (not isinstance(changes["title"], str) or not changes["title"].strip()):
            raise ValueError("title must be nonempty")
        if "descriptionHtml" in changes and not isinstance(changes["descriptionHtml"], str):
            raise ValueError("descriptionHtml must be text")
        if "seo" in changes:
            seo = changes["seo"]
            if not isinstance(seo, dict) or not seo or set(seo) - {"title", "description"} or any(not isinstance(v, str) for v in seo.values()):
                raise ValueError("Invalid SEO fields")
    return raw


def prepare_manifest(path: str, output: str) -> dict:
    """Fetch authoritative current snapshots for operator-provided product IDs."""
    ids = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(ids, list) or not ids:
        raise ValueError("Product ID input must be a nonempty JSON list")
    seen = set()
    manifest = []
    for identifier in ids:
        gid = product_gid(str(identifier))
        if gid in seen:
            raise ValueError("Duplicate product ID")
        seen.add(gid)
        product = shopify_graphql(PRODUCT_QUERY, {"id": gid}).get("product")
        if not product:
            raise RuntimeError(f"Cannot fetch product {gid}")
        manifest.append({
            "id": gid,
            "expected_sha256": snapshot_hash(product),
            "changes": suggested_content(product),
            "approved": False,
        })
    # deliberately not a valid apply-manifest until an operator has checked the content
    write_report(manifest, output)
    return {"prepared": len(manifest), "path": output, "approved": 0}


def apply_manifest(path: str, log_path: str, confirm: bool, limit: int, delay: float) -> dict:
    if not confirm:
        raise ValueError("Live updates require --confirm after explicit merchant approval")
    if limit < 1 or limit > 100:
        raise ValueError("--limit must be between 1 and 100")
    if delay < 0:
        raise ValueError("--delay must be nonnegative")
    manifest = load_manifest(path)
    if len(manifest) > limit:
        raise ValueError(f"Batch size {len(manifest)} exceeds --limit {limit}")
    target = Path(log_path)
    if target.exists():
        raise FileExistsError("Refusing to overwrite an existing update log")
    target.parent.mkdir(parents=True, exist_ok=True)
    # Write append-only audit log as work proceeds. Keep it private.
    changed = 0
    with target.open("x", encoding="utf-8") as output:
        for entry in manifest:
            gid = product_gid(str(entry["id"]))
            original = shopify_graphql(PRODUCT_QUERY, {"id": gid}).get("product")
            if not original:
                raise RuntimeError(f"Product missing, aborted at {gid}; inspect audit log")
            if snapshot_hash(original) != entry["expected_sha256"]:
                raise RuntimeError(f"Product changed since approval; aborted at {gid}; inspect audit log")
            output.write(json.dumps({"id": gid, "status": "before", "snapshot": stable_snapshot(original)}) + "\n")
            output.flush()
            result = shopify_graphql(UPDATE_MUTATION, {"product": {"id": gid, **entry["changes"]}})
            payload = result.get("productUpdate") or {}
            if payload.get("userErrors"):
                output.write(json.dumps({"id": gid, "status": "failed", "errors": payload["userErrors"]}) + "\n")
                output.flush()
                raise RuntimeError(f"Shopify rejected {gid}; stopped. See log")
            output.write(json.dumps({"id": gid, "status": "updated"}) + "\n")
            output.flush()
            changed += 1
            if changed < len(manifest):
                time.sleep(delay)
    return {"updated": changed, "log": str(target)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("analyze", "prepare", "apply"))
    parser.add_argument("--input", help="CSV for analyze; JSON ID list for prepare; JSON manifest for apply")
    parser.add_argument("--output", help="New JSON output path")
    parser.add_argument("--confirm", action="store_true", help="Permit approved live Shopify writes")
    parser.add_argument("--limit", type=int, default=25, help="Maximum products per apply run, capped at 100")
    parser.add_argument("--delay", type=float, default=0.75, help="Seconds between writes")
    args = parser.parse_args()
    if not args.input or not args.output:
        parser.error("--input and --output are required")
    if args.command == "analyze":
        result = analyze_feed(args.input)
        write_report(result, args.output)
        print(json.dumps({"products_scanned": result["products_scanned"],
                          "drafts": len(result["drafts"]), "output": args.output}, indent=2))
    elif args.command == "prepare":
        print(json.dumps(prepare_manifest(args.input, args.output), indent=2))
    else:
        print(json.dumps(apply_manifest(args.input, args.output, args.confirm, args.limit, args.delay), indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, OSError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
