"""Create one reviewed Shopify product as a DRAFT; never publish automatically.

No third-party dependencies. The merchant must explicitly authorize every creation.
Existing product-page audit/update operations remain in shopify_product_pages.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

from tools.shopify_product_pages import shopify_graphql

CREATE_MUTATION = """
mutation CreateReviewedDraft($product: ProductCreateInput!, $media: [CreateMediaInput!]) {
  productCreate(product: $product, media: $media) {
    product { id title handle status }
    userErrors { field message }
  }
}
"""
FIELDS = {"title", "descriptionHtml", "vendor", "productType", "handle", "seo", "tags", "images"}
HANDLE_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def validated_product(spec: dict) -> dict:
    if not isinstance(spec, dict) or set(spec) - FIELDS:
        raise ValueError("Product must be an object with only supported fields: " + ", ".join(sorted(FIELDS)))
    if not isinstance(spec.get("title"), str) or not spec["title"].strip():
        raise ValueError("A non-empty product title is required")
    product = {"title": spec["title"].strip(), "status": "DRAFT"}
    for name in ("descriptionHtml", "vendor", "productType"):
        if name in spec:
            if not isinstance(spec[name], str):
                raise ValueError(name + " must be text")
            product[name] = spec[name]
    if "handle" in spec:
        if not isinstance(spec["handle"], str) or not HANDLE_PATTERN.fullmatch(spec["handle"]):
            raise ValueError("handle must use lowercase letters, numbers and hyphens")
        product["handle"] = spec["handle"]
    if "seo" in spec:
        seo = spec["seo"]
        if not isinstance(seo, dict) or not seo or set(seo) - {"title", "description"} or not all(isinstance(v, str) for v in seo.values()):
            raise ValueError("seo must be an object with title and/or description text")
        product["seo"] = seo
    if "tags" in spec:
        tags = spec["tags"]
        if not isinstance(tags, list) or len(tags) > 30 or not all(isinstance(v, str) and v.strip() for v in tags):
            raise ValueError("tags must be a list of up to 30 non-empty strings")
        product["tags"] = tags
    return product


def validated_media(spec: dict) -> list[dict]:
    images = spec.get("images", [])
    if not isinstance(images, list) or len(images) > 10:
        raise ValueError("images must be a list of at most 10 image URLs")
    result = []
    for image in images:
        if not isinstance(image, dict) or set(image) - {"url", "alt"} or not isinstance(image.get("url"), str):
            raise ValueError("Each image must have a url and optional alt text")
        url = image["url"]
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
            raise ValueError("Each image must have a public HTTPS URL")
        if "alt" in image and not isinstance(image["alt"], str):
            raise ValueError("Image alt must be text")
        result.append({"originalSource": url, "mediaContentType": "IMAGE", "alt": image.get("alt", "")})
    return result


def load_spec(path: str) -> dict:
    spec = json.loads(Path(path).read_text(encoding="utf-8"))
    validated_product(spec)
    validated_media(spec)
    return spec


def fingerprint(spec: dict) -> str:
    return hashlib.sha256(json.dumps(spec, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def draft_preview(spec: dict) -> dict:
    return {
        "input_sha256": fingerprint(spec),
        "product": validated_product(spec),
        "media": validated_media(spec),
        "will_create": "one unpublished Shopify DRAFT product; no variants/prices/inventory settings or publication",
        "created": False,
    }


def create_draft(spec: dict, approval_sha256: str, *, confirmed: bool) -> dict:
    preview = draft_preview(spec)
    if not confirmed or not re.fullmatch(r"[a-f0-9]{64}", approval_sha256 or ""):
        raise ValueError("Explicit --confirm and the preview's --approve-sha256 are required")
    if approval_sha256 != preview["input_sha256"]:
        raise ValueError("Product content changed since preview; review and approve again")
    response = shopify_graphql(CREATE_MUTATION, {"product": preview["product"], "media": preview["media"]})
    payload = response.get("productCreate") or {}
    if payload.get("userErrors"):
        raise RuntimeError("Shopify rejected draft creation: " + json.dumps(payload["userErrors"]))
    product = payload.get("product")
    if not isinstance(product, dict) or not product.get("id"):
        raise RuntimeError("Shopify did not return a created product ID; verify in Shopify before retrying")
    if product.get("status") != "DRAFT":
        raise RuntimeError("Created product did not return DRAFT status; verify immediately in Shopify")
    return {"created": True, "product": product, "input_sha256": preview["input_sha256"], "published": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preview", "create"))
    parser.add_argument("--input", required=True, help="Merchant-verified JSON product specification")
    parser.add_argument("--approve-sha256", help="SHA-256 from the preview for this exact source")
    parser.add_argument("--confirm", action="store_true", help="Explicit merchant approval to create exactly one draft")
    args = parser.parse_args()
    spec = load_spec(args.input)
    result = draft_preview(spec) if args.command == "preview" else create_draft(
        spec, args.approve_sha256 or "", confirmed=args.confirm
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, OSError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
