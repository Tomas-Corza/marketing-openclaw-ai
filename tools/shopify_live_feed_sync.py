"""Authorized Shopify GraphQL catalog -> Merchant Center feed generation.

Standard library only. Queries all product variants with pagination, validates with the
existing feed builder, and writes a feed and rejection report. No Shopify writes.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import tempfile
import time
from pathlib import Path

try:
    from tools.shopify_feed_builder import convert, save, shop_domain
    from tools.shopify_product_pages import shopify_graphql
except ModuleNotFoundError:
    from shopify_feed_builder import convert, save, shop_domain
    from shopify_product_pages import shopify_graphql

QUERY = """
query MerchantFeedVariants($first: Int!, $after: String) {
  productVariants(first: $first, after: $after) {
    pageInfo { hasNextPage endCursor }
    nodes {
      id legacyResourceId sku barcode price inventoryQuantity inventoryPolicy
      availableForSale
      inventoryItem { tracked }
      selectedOptions { name value }
      image { url }
      product {
        handle title descriptionHtml vendor status onlineStoreUrl
        featuredImage { url }
      }
    }
  }
}
"""
COLUMNS = [
    "Handle", "Title", "Body (HTML)", "Vendor", "Variant SKU",
    "Variant Price", "Variant Inventory Tracker", "Variant Inventory Qty",
    "Variant Inventory Policy", "Variant Barcode", "Image Src", "Variant Image",
    "Variant ID", "Status", "Published",
    "Option1 Value", "Option2 Value", "Option3 Value",
]


def graphql_pages(fetch=shopify_graphql, page_size: int = 100, max_pages: int = 1000):
    cursor = None
    cursors = set()
    for _ in range(max_pages):
        payload = fetch(QUERY, {"first": page_size, "after": cursor})
        connection = payload.get("productVariants")
        if not isinstance(connection, dict):
            raise RuntimeError("Invalid Shopify API response: missing productVariants")
        for node in connection.get("nodes") or []:
            yield node
        page = connection.get("pageInfo") or {}
        if not page.get("hasNextPage"):
            return
        cursor = page.get("endCursor")
        if not cursor or cursor in cursors:
            raise RuntimeError("Shopify API returned a missing or repeated pagination cursor")
        cursors.add(cursor)
    raise RuntimeError("Shopify catalog exceeded max pages; feed creation aborted")


def variant_row(node: dict) -> dict | None:
    product = node.get("product") or {}
    if product.get("status") != "ACTIVE" or not product.get("onlineStoreUrl"):
        return None
    ident = str(node.get("legacyResourceId") or "").strip()
    if not ident.isdigit():
        raise ValueError("Variant missing stable numeric Shopify ID")
    image = (node.get("image") or product.get("featuredImage") or {}).get("url") or ""
    # Shopify's onlineStoreUrl confirms published online storefront visibility.
    options = [x.get("value", "") for x in (node.get("selectedOptions") or []) if isinstance(x, dict)]
    tracked = (node.get("inventoryItem") or {}).get("tracked")
    quantity = node.get("inventoryQuantity")
    return {
        "Handle": product.get("handle") or "",
        "Title": product.get("title") or "",
        "Body (HTML)": product.get("descriptionHtml") or "",
        "Vendor": product.get("vendor") or "",
        # Numeric variant ID is more stable than merchant-edited SKU and always unique.
        "Variant SKU": "shopify-variant-" + ident,
        "Variant Price": node.get("price") or "",
        "Variant Inventory Tracker": "shopify" if tracked else "",
        "Variant Inventory Qty": str(quantity) if quantity is not None else "",
        "Variant Inventory Policy": str(node.get("inventoryPolicy") or "").lower(),
        "Variant Barcode": node.get("barcode") or "",
        "Image Src": (product.get("featuredImage") or {}).get("url") or "",
        "Variant Image": image,
        "Variant ID": ident,
        "Status": "active",
        "Published": "true",
        "Option1 Value": options[0] if len(options)>0 else "",
        "Option2 Value": options[1] if len(options)>1 else "",
        "Option3 Value": options[2] if len(options)>2 else "",
    }


def write_catalog_csv(path: str, nodes: list[dict]) -> dict:
    stats = {"variants_seen": len(nodes), "unpublished_skipped": 0}
    with open(path, "w", encoding="utf-8", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=COLUMNS)
        writer.writeheader()
        for node in nodes:
            row = variant_row(node)
            if row is None:
                stats["unpublished_skipped"] += 1
                continue
            writer.writerow(row)
    return stats


def run(output: str, rejects: str, store_url: str, currency: str, fmt: str,
        allow_untracked: bool, strict: bool, fetch=shopify_graphql) -> dict:
    shop_domain(store_url)
    out = Path(output)
    rejected = Path(rejects)
    if out.exists() or rejected.exists():
        raise FileExistsError("Output paths must not already exist; use fresh build directories")
    nodes = list(graphql_pages(fetch))
    if not nodes:
        raise RuntimeError("Shopify API returned no product variants; refusing to replace feed")
    with tempfile.TemporaryDirectory() as temp:
        catalog = str(Path(temp) / "catalog.csv")
        stats = write_catalog_csv(catalog, nodes)
        result = convert(catalog, store_url, currency=currency, allow_untracked=allow_untracked)
    if not result["items"]:
        raise RuntimeError("No valid published variants; feed not generated")
    if strict and result["rejected"]:
        reasons = result["summary"]["reasons"]
        raise RuntimeError(f"Strict mode: rejected {len(result['rejected'])} variants; refusing to deploy. Reasons: {json.dumps(reasons)}")
    save(result, output, rejects, fmt, store_url)
    return {**stats, **result["summary"], "feed": output, "reject_report": rejects}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--store-url", required=True, help="Verified HTTPS customer storefront origin")
    p.add_argument("--output", required=True)
    p.add_argument("--rejects", required=True)
    p.add_argument("--currency", default="USD")
    p.add_argument("--format", choices=("rss", "tsv"), default="rss")
    p.add_argument("--untracked-in-stock", action="store_true", help="Only if merchant confirms untracked inventory available")
    p.add_argument("--allow-partial", action="store_true", help="Permit valid rows when some variants are rejected")
    args = p.parse_args()
    if not os.getenv("SHOPIFY_SHOP_DOMAIN") or not os.getenv("SHOPIFY_ACCESS_TOKEN"):
        p.error("Authorized SHOPIFY_SHOP_DOMAIN and SHOPIFY_ACCESS_TOKEN required")
    print(json.dumps(run(args.output, args.rejects, args.store_url, args.currency, args.format,
                         args.untracked_in_stock, strict=not args.allow_partial), indent=2))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError) as exc:
        print("Error:", exc, file=sys.stderr)
        sys.exit(1)
