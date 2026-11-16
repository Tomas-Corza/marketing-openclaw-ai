"""Read-only Google Merchant API products.list adapter.

Requires a short-lived OAuth 2.0 access token with content scope and merchant account
permission. This script never edits Merchant Center products or account settings.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://merchantapi.googleapis.com/products/v1"


def list_products(account_id: str, access_token: str, *,
                  page_size: int = 250, max_pages: int = 1000, opener=None) -> dict:
    if not re.fullmatch(r"[0-9]+", account_id):
        raise ValueError("Merchant account ID must be numeric")
    if not access_token:
        raise ValueError("A short-lived OAuth access token is required")
    if not 1 <= page_size <= 1000 or max_pages < 1:
        raise ValueError("Invalid pagination limits")
    if opener is None:
        opener = urllib.request.urlopen
    results = []
    cursor = None
    seen = set()
    for _ in range(max_pages):
        query = {"pageSize": str(page_size)}
        if cursor:
            query["pageToken"] = cursor
        url = BASE + "/accounts/" + account_id + "/products?" + urllib.parse.urlencode(query)
        req = urllib.request.Request(
            url,
            headers={"Authorization": "Bearer " + access_token, "Accept": "application/json"},
        )
        try:
            with opener(req, timeout=30) as response:
                payload = json.load(response)
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"Merchant API HTTP {exc.code}; check OAuth scope, account rights and quotas") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError("Merchant API connection failed") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("products", []), list):
            raise RuntimeError("Unexpected Merchant API response")
        results.extend(payload.get("products", []))
        cursor = payload.get("nextPageToken")
        if not cursor:
            return {"products": results, "product_count": len(results),
                    "source": "Google Merchant API products.list"}
        if cursor in seen:
            raise RuntimeError("Merchant API repeated pageToken")
        seen.add(cursor)
    raise RuntimeError("Exceeded maximum Merchant API pages; refusing partial snapshot")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--account-id", required=True, help="Authorized Merchant Center account ID")
    p.add_argument("--output", required=True, help="Private output JSON file (must not exist)")
    p.add_argument("--page-size", type=int, default=250)
    args = p.parse_args()
    if Path(args.output).exists():
        p.error("Refusing to overwrite existing snapshot")
    token = os.getenv("MERCHANT_API_ACCESS_TOKEN", "")
    result = list_products(args.account_id, token, page_size=args.page_size)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"products": result["product_count"], "output": args.output}))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, RuntimeError) as exc:
        print("Error:", exc, file=sys.stderr)
        sys.exit(1)
