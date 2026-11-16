"""Offline tests for feed diagnostics and Merchant API adapter; no credentials needed."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.merchant_feed_diagnostics import (
    audit, normalize_merchant_products, draft_manifest,
    apply_approved, fingerprint, check_gtin, load_tsv, load_rss,
    write_feed_tsv, write_feed_rss,
)
from tools.merchant_api_connector import list_products

GOOD = {
    "id": "sku-1", "title": "Desk Lamp", "description": "A desk lamp.",
    "link": "https://shop.example/products/desk-lamp",
    "image_link": "https://cdn.example/lamp.jpg",
    "availability": "in_stock", "price": "35.00 USD",
    "brand": "Sample", "gtin": "012345678905",
}

class DiagnosticsTests(unittest.TestCase):
    def test_healthy_product(self):
        self.assertEqual(audit([GOOD])["issues"], [])

    def test_detects_disapproval_and_offline_errors(self):
        bad = dict(GOOD, id="sku-bad", price="0.00 USD", gtin="1234",
                   availability="perhaps", image_link="http://broken.example/image.jpg")
        issues = audit([bad])["issues"]
        codes = {x["code"] for x in issues}
        self.assertTrue({"invalid_price", "invalid_gtin", "invalid_availability", "invalid_image_link"}.issubset(codes))

    def test_duplicate_ids(self):
        self.assertIn("duplicate_id", [x["code"] for x in audit([GOOD, GOOD])["issues"]])

    def test_gtin_checksum(self):
        self.assertTrue(check_gtin("012345678905"))
        self.assertFalse(check_gtin("012345678904"))

    def test_normalize_merchant_api_snapshot(self):
        data = {"products": [{
            "offerId": "sku-1",
            "productStatus": {
                "destinationStatuses": [{"disapprovedCountries": ["US"]}],
                "itemLevelIssues": [{
                    "code": "invalid_gtin", "severity": "DISAPPROVED",
                    "attribute": "gtins", "description": "Invalid GTIN",
                    "applicableCountries": ["US"],
                }],
            },
        }]}
        result = normalize_merchant_products(data)
        self.assertEqual(result["disapproved_products"], 1)
        self.assertEqual(result["issues"][0]["priority"], "critical")

    def test_fix_requires_explicit_approval_and_snapshot(self):
        manifest = draft_manifest([GOOD], {"sku-1": {"title": "Reviewed Desk Lamp"}})
        self.assertIs(manifest[0]["approved"], False)
        with self.assertRaisesRegex(ValueError, "explicit approval"):
            apply_approved([GOOD], manifest)
        manifest[0]["approved"] = True
        result = apply_approved([GOOD], manifest)
        self.assertEqual(result[0]["title"], "Reviewed Desk Lamp")
        self.assertEqual(GOOD["title"], "Desk Lamp")
        changed = dict(GOOD, price="99.99 USD")
        with self.assertRaisesRegex(ValueError, "changed since approval"):
            apply_approved([changed], manifest)

    def test_prevents_commercial_data_edits(self):
        with self.assertRaises(ValueError):
            draft_manifest([GOOD], {"sku-1": {"price": "1.00 USD"}})

    def test_tsv_rss_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            tsv = str(Path(tmp) / "feed.tsv")
            rss = str(Path(tmp) / "feed.xml")
            write_feed_tsv(tsv, [GOOD])
            write_feed_rss(rss, [GOOD])
            self.assertEqual(load_tsv(tsv)[0]["id"], GOOD["id"])
            self.assertEqual(load_rss(rss)[0]["id"], GOOD["id"])


class MerchantAPITests(unittest.TestCase):
    def test_page_token_pagination(self):
        urls = []
        class Response:
            def __init__(self, content): self.content = content
            def __enter__(self): return self
            def __exit__(self, *_): return False
            def read(self): return json.dumps(self.content).encode()
        def fetch(request, timeout=30):
            urls.append(request.full_url)
            if len(urls) == 1:
                return Response({"products": [{"offerId": "sku-1"}], "nextPageToken": "next"})
            return Response({"products": [{"offerId": "sku-2"}]})
        result = list_products("123456", "test-token", opener=fetch)
        self.assertEqual(result["product_count"], 2)
        self.assertIn("pageToken=next", urls[1])

    def test_account_validation(self):
        with self.assertRaises(ValueError):
            list_products("../other", "token")


if __name__ == "__main__":
    unittest.main()
