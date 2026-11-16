"""Shopify product-page audit and human-approved update utility (GraphQL Admin API 2026-10).

No third-party Python dependencies. Never commit access tokens or customer data.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

VERSION = "2026-10"
PRODUCT_QUERY = """
query ProductPage($id: ID!) {
  product(id: $id) {
    id title handle descriptionHtml vendor productType
    seo { title description }
  }
}
"""
UPDATE_MUTATION = """
mutation UpdateProductPage($product: ProductUpdateInput!) {
  productUpdate(product: $product) {
    product { id title descriptionHtml seo { title description } }
    userErrors { field message }
  }
}
"""
ALLOWED = {"title", "descriptionHtml", "seo"}


def product_gid(value: str) -> str:
    if re.fullmatch(r"[0-9]+", value):
        return f"gid://shopify/Product/{value}"
    if re.fullmatch(r"gid://shopify/Product/[0-9]+", value):
        return value
    raise ValueError("Use a numeric Shopify product ID or a Product GID")


def audit(product: dict) -> dict:
    title = (product.get("title") or "").strip()
    html = product.get("descriptionHtml") or ""
    plain = re.sub(r"<[^>]+>", " ", html)
    plain = re.sub(r"\s+", " ", plain).strip()
    seo = product.get("seo") or {}
    findings = []
    if not title:
        findings.append("Missing product title")
    if len(plain) < 100:
        findings.append("Description contains fewer than 100 plain-text characters")
    if not (seo.get("title") or "").strip():
        findings.append("Missing custom SEO title")
    if not (seo.get("description") or "").strip():
        findings.append("Missing custom SEO description")
    return {"product_id": product.get("id"), "title": title,
            "description_characters": len(plain), "findings": findings,
            "recommendation": "Draft changes using verified product facts and customer needs; review before publishing."}


def shopify_graphql(query: str, variables: dict) -> dict:
    shop = os.environ.get("SHOPIFY_SHOP_DOMAIN", "")
    token = os.environ.get("SHOPIFY_ACCESS_TOKEN", "")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.-]*\.myshopify\.com", shop):
        raise RuntimeError("SHOPIFY_SHOP_DOMAIN must be a valid *.myshopify.com domain")
    if not token:
        raise RuntimeError("Set SHOPIFY_ACCESS_TOKEN in your local environment")
    url = f"https://{shop}/admin/api/{VERSION}/graphql.json"
    body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    request = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Content-Type": "application/json", "X-Shopify-Access-Token": token})
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Shopify HTTP error {exc.code}; check permissions, API version and rate limits") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError("Shopify network request failed") from exc
    if payload.get("errors"):
        raise RuntimeError("Shopify GraphQL errors: " + json.dumps(payload["errors"]))
    return payload.get("data") or {}


def load_proposal(path: str) -> dict:
    proposal = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(proposal, dict) or not proposal:
        raise ValueError("Proposal must be a nonempty JSON object")
    if set(proposal) - ALLOWED:
        raise ValueError("Only title, descriptionHtml, and seo are allowed in proposals")
    if "title" in proposal and (not isinstance(proposal["title"], str) or not proposal["title"].strip()):
        raise ValueError("title must be nonempty text")
    if "descriptionHtml" in proposal and not isinstance(proposal["descriptionHtml"], str):
        raise ValueError("descriptionHtml must be text")
    if "seo" in proposal:
        seo = proposal["seo"]
        if not isinstance(seo, dict) or not seo or set(seo) - {"title", "description"}:
            raise ValueError("seo must contain title and/or description")
        if not all(isinstance(v, str) for v in seo.values()):
            raise ValueError("SEO values must be text")
    return proposal


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("audit", "fetch", "preview", "apply"))
    parser.add_argument("--input", help="Local product JSON for offline audit")
    parser.add_argument("--id", help="Shopify numeric product ID or GID")
    parser.add_argument("--proposal", help="JSON file of proposed content changes")
    parser.add_argument("--confirm", action="store_true", help="Required with apply to write changes")
    args = parser.parse_args()

    if args.command == "audit":
        if not args.input:
            parser.error("audit requires --input")
        product = json.loads(Path(args.input).read_text(encoding="utf-8"))
        result = audit(product)
    else:
        if not args.id:
            parser.error("fetch/preview/apply require --id")
        gid = product_gid(args.id)
        if args.command == "fetch":
            result = shopify_graphql(PRODUCT_QUERY, {"id": gid}).get("product")
            if not result:
                raise RuntimeError("Product not found or inaccessible")
        else:
            if not args.proposal:
                parser.error("preview/apply require --proposal")
            changes = load_proposal(args.proposal)
            current = shopify_graphql(PRODUCT_QUERY, {"id": gid}).get("product")
            if not current:
                raise RuntimeError("Product not found or inaccessible")
            if args.command == "preview":
                result = {"product_id": gid, "current": current, "proposed": changes,
                          "published": False}
            else:
                if not args.confirm:
                    parser.error("apply requires --confirm; preview changes first")
                response = shopify_graphql(UPDATE_MUTATION, {"product": {"id": gid, **changes}})
                update = response.get("productUpdate") or {}
                if update.get("userErrors"):
                    raise RuntimeError("Shopify rejected update: " + json.dumps(update["userErrors"]))
                result = {"published": True, "product": update.get("product")}
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, OSError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
