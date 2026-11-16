"""Create Google Merchant Center TSV or RSS XML feeds from authorized Shopify CSV exports.

Offline, standard-library only; never connects to a merchant account or publishes a feed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import quote, urlparse

try:
    from tools.shopify_bulk_feed import plain_text
except ModuleNotFoundError:
    from shopify_bulk_feed import plain_text

FIELDS = [
    "id", "title", "description", "link", "image_link", "availability",
    "price", "condition", "brand", "gtin", "mpn", "item_group_id",
]
REQUIRED_SOURCE = {"Handle", "Title", "Body (HTML)", "Variant Price", "Variant SKU"}
NS = "http://base.google.com/ns/1.0"


def shop_domain(value: str) -> str:
    url = value.strip().rstrip("/")
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ("", "/"):
        raise ValueError("--store-url must be the HTTPS root of the verified storefront")
    if parsed.port is not None:
        raise ValueError("--store-url must not include a port")
    return url


def price(value: str, currency: str) -> str:
    try:
        number = Decimal(value.strip())
    except (InvalidOperation, AttributeError):
        raise ValueError("Missing or invalid variant price")
    if not number.is_finite() or number <= 0 or number.as_tuple().exponent < -2:
        raise ValueError("Price must be positive with at most two decimal places")
    return f"{number:.2f} {currency}"


def availability(row: dict, allow_untracked: bool) -> str:
    tracker = (row.get("Variant Inventory Tracker") or "").strip().lower()
    quantity = (row.get("Variant Inventory Qty") or "").strip()
    if tracker:
        try:
            count = int(quantity)
        except ValueError:
            raise ValueError("Tracked inventory requires numeric Variant Inventory Qty")
        if count > 0:
            return "in_stock"
        # Shopify continue-selling does not prove shipping availability. Review separately.
        if (row.get("Variant Inventory Policy") or "").strip().lower() == "continue":
            raise ValueError("Continue-selling with no stock requires merchant availability review")
        return "out_of_stock"
    if not allow_untracked:
        raise ValueError("Untracked inventory is unknown; use --untracked-in-stock only after merchant verification")
    return "in_stock"


def variant_key(row: dict) -> str:
    handle = (row.get("Handle") or "").strip()
    sku = (row.get("Variant SKU") or "").strip()
    if not sku:
        raise ValueError("Missing variant SKU (required for stable item IDs)")
    return sku


def iter_catalog(path: str):
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not REQUIRED_SOURCE.issubset(reader.fieldnames):
            raise ValueError("Shopify CSV missing required columns: " + ", ".join(sorted(REQUIRED_SOURCE)))
        parents = {}
        current = None
        records = []
        for line, raw in enumerate(reader, 2):
            key = (raw.get("Handle") or "").strip()
            if not key:
                continue
            if key not in parents:
                parents[key] = {"Title": "", "Body (HTML)": "", "Vendor": "", "Image Src": ""}
            parent = parents[key]
            for field in parent:
                if raw.get(field) and not parent[field]:
                    parent[field] = raw[field].strip()
            # Variant SKU/Price, not image-only Shopify export rows, determines sellable item.
            if (raw.get("Variant SKU") or "").strip() or (raw.get("Variant Price") or "").strip():
                records.append((line, key, raw))
    for line, handle, row in records:
        yield line, handle, row, parents[handle]


def build_item(handle: str, row: dict, parent: dict, store: str,
               currency: str, condition: str, allow_untracked: bool) -> dict:
    ident = variant_key(row)
    status = (row.get("Status") or "").strip().lower()
    published = (row.get("Published") or "").strip().lower()
    if status and status != "active":
        raise ValueError("Product is not active")
    if published in ("false", "no", "0"):
        raise ValueError("Product is not published")
    title = parent["Title"].strip()
    if not title:
        raise ValueError("Missing product title")
    option_values = []
    for i in range(1, 4):
        option = (row.get(f"Option{i} Value") or "").strip()
        if option and option.lower() != "default title":
            option_values.append(option)
    variant_title = title if not option_values else title + " - " + " / ".join(option_values)
    description = plain_text(parent.get("Body (HTML)") or "")
    if not description:
        raise ValueError("Missing product description")
    image = (row.get("Variant Image") or row.get("Image Src") or parent.get("Image Src") or "").strip()
    if not image.startswith("https://"):
        raise ValueError("Missing valid HTTPS image URL")
    image_parsed = urlparse(image)
    if not image_parsed.hostname:
        raise ValueError("Invalid image URL")
    product_link = store + "/products/" + quote(handle, safe="")
    # Shopify variant IDs are often absent from CSV exports; require merchant to verify variant link behavior.
    result = {
        "id": ident,
        "title": variant_title[:150],
        "description": description[:5000],
        "link": product_link,
        "image_link": image,
        "availability": availability(row, allow_untracked),
        "price": price(row.get("Variant Price") or "", currency),
        "condition": condition,
        "brand": (parent.get("Vendor") or "").strip(),
        "gtin": (row.get("Variant Barcode") or "").strip(),
        "mpn": "",
        "item_group_id": handle if option_values else "",
    }
    if not result["brand"] and not result["gtin"]:
        raise ValueError("Missing brand and GTIN; product identifiers need merchant review")
    return result


def convert(source: str, store_url: str, currency: str = "USD",
            condition: str = "new", allow_untracked: bool = False) -> dict:
    store = shop_domain(store_url)
    if not re.fullmatch(r"[A-Z]{3}", currency):
        raise ValueError("Currency must be a three-letter ISO code such as USD")
    if condition not in ("new", "used", "refurbished"):
        raise ValueError("Unsupported condition")
    accepted, rejected = [], []
    ids = set()
    reasons = Counter()
    for line, handle, row, parent in iter_catalog(source):
        try:
            item = build_item(handle, row, parent, store, currency, condition, allow_untracked)
            if item["id"] in ids:
                raise ValueError("Duplicate SKU across variants; resolve before publishing")
            ids.add(item["id"])
            accepted.append(item)
        except ValueError as exc:
            reasons[str(exc)] += 1
            rejected.append({"row": line, "handle": handle, "sku": (row.get("Variant SKU") or ""), "reason": str(exc)})
    return {"items": accepted, "rejected": rejected,
            "summary": {"accepted": len(accepted), "rejected": len(rejected), "reasons": dict(reasons)}}


def save(result: dict, output: str, rejects_path: str, fmt: str, store_url: str):
    out, reject_file = Path(output), Path(rejects_path)
    if out.resolve() == reject_file.resolve():
        raise ValueError("Output feed and reject-report paths must differ")
    if out.exists() or reject_file.exists():
        raise FileExistsError("Refusing to overwrite existing feed or reject report")
    out.parent.mkdir(parents=True, exist_ok=True)
    reject_file.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "tsv":
        with out.open("x", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS, delimiter="\t", extrasaction="ignore")
            writer.writeheader()
            writer.writerows(result["items"])
    elif fmt == "rss":
        ET.register_namespace("g", NS)
        root = ET.Element("rss", version="2.0")
        channel = ET.SubElement(root, "channel")
        ET.SubElement(channel, "title").text = "Shopify product feed"
        ET.SubElement(channel, "link").text = store_url
        ET.SubElement(channel, "description").text = "Merchant product catalog export"
        for item in result["items"]:
            child = ET.SubElement(channel, "item")
            for field in FIELDS:
                if item.get(field):
                    if field in ("title", "description", "link"):
                        ET.SubElement(child, field).text = item[field]
                    else:
                        ET.SubElement(child, f"{{{NS}}}{field}").text = item[field]
        with out.open("xb") as stream:
            ET.ElementTree(root).write(stream, encoding="utf-8", xml_declaration=True)
    else:
        raise ValueError("Unsupported format")
    with reject_file.open("x", encoding="utf-8") as stream:
        json.dump({"summary": result["summary"], "rejected": result["rejected"]}, stream, indent=2)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Authorized Shopify products CSV export")
    parser.add_argument("--store-url", required=True, help="Verified HTTPS storefront URL")
    parser.add_argument("--output", required=True, help="New output feed file")
    parser.add_argument("--rejects", required=True, help="New JSON validation report file")
    parser.add_argument("--format", choices=("tsv", "rss"), default="tsv")
    parser.add_argument("--currency", default="USD", help="Must reflect actual storefront prices; defaults USD")
    parser.add_argument("--condition", choices=("new", "used", "refurbished"), default="new",
                        help="Verify this applies to every item")
    parser.add_argument("--untracked-in-stock", action="store_true",
                        help="ONLY if merchant confirms all untracked variants are in stock")
    args = parser.parse_args()
    result = convert(args.input, args.store_url, args.currency, args.condition, args.untracked_in_stock)
    if not result["items"]:
        raise ValueError("No valid products; feed not written. Check source and inventory fields")
    save(result, args.output, args.rejects, args.format, args.store_url)
    print(json.dumps({"feed": args.output, "rejects": args.rejects, **result["summary"]}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        print("Error:", exc, file=sys.stderr)
        sys.exit(1)
