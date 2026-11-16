"""Review-first CSV -> Shopify DRAFT product importer using productSet (GraphQL 2026-10).

One CSV row per variant; products grouped by unique handle. No AI generation,
publication, inventory changes, or updates to existing Shopify products.
"""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys

from tools.shopify_product_pages import shopify_graphql

PRODUCT_SET = """
mutation CreateDraftWithVariants($input: ProductSetInput!) {
  productSet(input: $input, synchronous: true) {
    product { id handle title status variants(first: 100) { nodes { id sku price } } }
    userErrors { field message code }
  }
}
"""
LOOKUP = """
query CheckExistingHandle($query: String!) {
  products(first: 5, query: $query) { nodes { id handle } }
}
"""
COLUMNS = (
    "handle", "title", "description_html", "vendor", "product_type",
    "seo_title", "seo_description", "tags",
    "option1_name", "option1_value", "option2_name", "option2_value",
    "option3_name", "option3_value", "sku", "price",
)
PRODUCT_FIELDS = ("title", "description_html", "vendor", "product_type", "seo_title", "seo_description", "tags")
HANDLE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PRICE = re.compile(r"^(?:0|[1-9][0-9]*)(?:\.[0-9]{1,2})?$")
MAX_ROWS = 1000
MAX_PRODUCTS = 100
MAX_VARIANTS = 100


def parse_csv(source: bytes) -> list[dict]:
    if not source or len(source) > 2_000_000:
        raise ValueError("CSV must be nonempty and at most 2 MB")
    try:
        text = source.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError("CSV must contain unique column headers")
        if set(reader.fieldnames) != set(COLUMNS):
            raise ValueError("CSV headers must exactly match the documented template")
        rows = []
        for record in reader:
            if None in record or any(value is None for value in record.values()):
                raise ValueError("CSV row has an unexpected number of fields")
            rows.append({key: value.strip() for key, value in record.items()})
            if len(rows) > MAX_ROWS:
                raise ValueError("CSV exceeds the 1,000-row maximum")
    except (UnicodeError, csv.Error) as exc:
        raise ValueError("Invalid UTF-8 CSV: " + str(exc)) from exc
    if not rows:
        raise ValueError("CSV contains no products")
    return rows


def build_products(source: bytes) -> list[dict]:
    rows = parse_csv(source)
    grouped = {}
    skus = set()
    for number, row in enumerate(rows, 2):
        handle = row["handle"]
        if not HANDLE.fullmatch(handle):
            raise ValueError(f"Row {number}: invalid handle")
        if not row["title"]:
            raise ValueError(f"Row {number}: title required")
        sku = row["sku"]
        if not sku or sku.casefold() in skus:
            raise ValueError(f"Row {number}: SKU missing or duplicated across the import")
        skus.add(sku.casefold())
        if not PRICE.fullmatch(row["price"]):
            raise ValueError(f"Row {number}: price must be a non-negative decimal with at most two places")
        try:
            amount = Decimal(row["price"])
        except InvalidOperation as exc:
            raise ValueError(f"Row {number}: invalid price") from exc
        if amount > Decimal("99999999.99"):
            raise ValueError(f"Row {number}: price is too large")
        options = []
        for index in (1, 2, 3):
            name, value = row[f"option{index}_name"], row[f"option{index}_value"]
            if bool(name) != bool(value):
                raise ValueError(f"Row {number}: option {index} requires both name and value")
            if name:
                options.append((name, value))
        if not options:
            raise ValueError(f"Row {number}: specify at least one option, e.g. Style / Standard")
        if len({name.casefold() for name, _ in options}) != len(options):
            raise ValueError(f"Row {number}: repeated option names")
        shared = {key: row[key] for key in PRODUCT_FIELDS}
        if handle not in grouped:
            grouped[handle] = {"shared": shared, "option_names": [name for name, _ in options], "values": {}, "variants": [], "options_seen": set()}
        group = grouped[handle]
        if shared != group["shared"] or [name for name, _ in options] != group["option_names"]:
            raise ValueError(f"Row {number}: inconsistent product details or option names for handle {handle}")
        combo = tuple(value.casefold() for _, value in options)
        if combo in group["options_seen"]:
            raise ValueError(f"Row {number}: duplicate variant combination for handle {handle}")
        group["options_seen"].add(combo)
        for name, value in options:
            group["values"].setdefault(name, [])
            if value not in group["values"][name]:
                group["values"][name].append(value)
        group["variants"].append({
            "sku": sku, "price": str(amount.quantize(Decimal("0.01"))),
            "optionValues": [{"optionName": name, "name": value} for name, value in options],
        })
        if len(group["variants"]) > MAX_VARIANTS:
            raise ValueError(f"{handle}: more than {MAX_VARIANTS} variants")
        if len(grouped) > MAX_PRODUCTS:
            raise ValueError("Import exceeds the 100-product maximum")
    products = []
    for handle, group in grouped.items():
        shared = group["shared"]
        item = {
            "handle": handle, "title": shared["title"], "status": "DRAFT",
            "productOptions": [
                {"name": name, "position": index, "values": [{"name": v} for v in group["values"][name]]}
                for index, name in enumerate(group["option_names"], 1)
            ],
            "variants": group["variants"],
        }
        for source_key, target in (
            ("description_html", "descriptionHtml"), ("vendor", "vendor"), ("product_type", "productType")
        ):
            if shared[source_key]:
                item[target] = shared[source_key]
        seo = {}
        if shared["seo_title"]:
            seo["title"] = shared["seo_title"]
        if shared["seo_description"]:
            seo["description"] = shared["seo_description"]
        if seo:
            item["seo"] = seo
        if shared["tags"]:
            item["tags"] = [x.strip() for x in shared["tags"].split("|") if x.strip()]
        products.append(item)
    return products


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def preview(source: bytes) -> dict:
    products = build_products(source)
    return {
        "input_sha256": sha256(source), "product_count": len(products),
        "variant_count": sum(len(p["variants"]) for p in products),
        "products": products,
        "status": "DRAFT",
        "notice": "Preview only; creation requires merchant approval. Existing product handles are not updated.",
    }


def check_handle(handle: str) -> None:
    result = shopify_graphql(LOOKUP, {"query": "handle:" + handle})
    nodes = ((result.get("products") or {}).get("nodes") or [])
    if any(node.get("handle") == handle for node in nodes):
        raise ValueError(f"Shopify already contains product handle: {handle}")


def create_one(product: dict) -> dict:
    check_handle(product["handle"])
    result = shopify_graphql(PRODUCT_SET, {"input": product})
    payload = result.get("productSet") or {}
    if payload.get("userErrors"):
        raise RuntimeError("Shopify rejected product: " + json.dumps(payload["userErrors"]))
    created = payload.get("product")
    if not isinstance(created, dict) or not created.get("id") or created.get("status") != "DRAFT":
        raise RuntimeError("Shopify response was incomplete or not a DRAFT; inspect Shopify before retrying")
    return {"id": created["id"], "handle": created.get("handle"), "status": created["status"], "variant_count": len(product["variants"])}


def start_import(source: bytes, approval: str, confirm: bool, log_path: Path, max_products: int = 10) -> dict:
    details = preview(source)
    if not confirm or approval != details["input_sha256"]:
        raise ValueError("Require --confirm and --approve-sha256 matching the reviewed CSV")
    if not 1 <= max_products <= 25:
        raise ValueError("--max-products must be between 1 and 25")
    if len(details["products"]) > max_products:
        raise ValueError(f"Import has {len(details['products'])} products; use --max-products or split CSV into reviewed batches")
    # Require fresh, private journal. Never overwrite history; uncertain network outcomes require manual reconciliation.
    if log_path.is_symlink():
        raise ValueError("Journal must not be a symlink")
    fd = os.open(str(log_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    results = []
    with os.fdopen(fd, "w", encoding="utf-8") as log:
        def record(event: dict) -> None:
            log.write(json.dumps(event, sort_keys=True) + "\n")
            log.flush()
            os.fsync(log.fileno())
        record({"event": "approved_import", "input_sha256": details["input_sha256"], "products": len(details["products"])})
        for product in details["products"]:
            handle = product["handle"]
            record({"event": "attempt", "handle": handle})
            try:
                result = create_one(product)
            except Exception as exc:
                record({"event": "stopped", "handle": handle, "error": str(exc)})
                raise RuntimeError(f"Stopped at {handle}; check Shopify and private journal before retrying: {exc}") from exc
            record({"event": "created", **result})
            results.append(result)
    return {"created": results, "count": len(results), "published": False, "journal": str(log_path)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preview", "create"))
    parser.add_argument("--input", required=True)
    parser.add_argument("--approve-sha256")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--journal", help="Private, new JSONL log path required for creation")
    parser.add_argument("--max-products", type=int, default=10)
    args = parser.parse_args()
    source = Path(args.input).read_bytes()
    if args.command == "preview":
        result = preview(source)
    else:
        if not args.journal:
            parser.error("create requires --journal outside the repository")
        result = start_import(source, args.approve_sha256 or "", args.confirm, Path(args.journal), args.max_products)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, OSError, csv.Error) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
