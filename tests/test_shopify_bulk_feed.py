"""Offline tests for Shopify feed auditing and safe manifests."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.shopify_bulk_feed import (
    analyze_feed, load_feed, load_manifest, snapshot_hash,
    suggested_content, apply_manifest,
)


class ShopifyBulkFeedTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)

    def write(self, name, content):
        path = self.directory / name
        path.write_text(content, encoding="utf-8")
        return str(path)

    def test_deduplicates_shopify_variant_rows(self):
        csv_path = self.write(
            "feed.csv",
            'Handle,Title,Body (HTML),Vendor,SEO Title,SEO Description\n'
            'lamp,Desk Lamp,<p>Warm light</p>,Example,,\n'
            'lamp,,,,,\n'
            'chair,Chair,<p>Wood seat</p>,Example,,\n',
        )
        products = load_feed(csv_path)
        self.assertEqual(len(products), 2)
        report = analyze_feed(csv_path)
        self.assertEqual(report["products_scanned"], 2)
        self.assertEqual(len(report["drafts"]), 2)

    def test_missing_required_columns(self):
        csv_path = self.write("feed.csv", "Handle,Title\nlamp,Lamp\n")
        with self.assertRaises(ValueError):
            load_feed(csv_path)

    def test_does_not_invent_description_from_empty_body(self):
        self.assertEqual(suggested_content({
            "title": "Lamp", "descriptionHtml": "", "seo": {"title": "", "description": ""}
        }), {"seo": {"title": "Lamp"}})

    def test_manifest_requires_approval_and_safe_fields(self):
        product = {
            "title": "Lamp", "descriptionHtml": "<p>Short</p>",
            "seo": {"title": "", "description": ""},
        }
        entry = {
            "id": "123", "expected_sha256": snapshot_hash(product),
            "changes": {"seo": {"title": "Lamp Title"}}, "approved": False,
        }
        path = self.write("manifest.json", json.dumps([entry]))
        with self.assertRaises(ValueError):
            load_manifest(path)
        entry["approved"] = True
        self.write("manifest.json", json.dumps([entry]))
        self.assertEqual(len(load_manifest(path)), 1)
        entry["changes"] = {"price": "0.01"}
        self.write("manifest.json", json.dumps([entry]))
        with self.assertRaises(ValueError):
            load_manifest(path)

    def test_apply_requires_confirmation_and_does_not_call_api(self):
        path = self.write("manifest.json", "[]")
        with patch("tools.shopify_bulk_feed.shopify_graphql") as api:
            with self.assertRaises(ValueError):
                apply_manifest(path, str(self.directory / "log.jsonl"), False, 25, 0)
            api.assert_not_called()

    def test_stale_snapshot_aborts_before_mutation(self):
        entry = {
            "id": "123", "expected_sha256": "0" * 64,
            "changes": {"seo": {"title": "Approved"}},
            "approved": True,
        }
        path = self.write("manifest.json", json.dumps([entry]))
        current = {
            "id": "gid://shopify/Product/123", "title": "Live Changed",
            "descriptionHtml": "<p>Different</p>",
            "seo": {"title": "Existing", "description": ""},
        }
        with patch("tools.shopify_bulk_feed.shopify_graphql", return_value={"product": current}) as api:
            with self.assertRaisesRegex(RuntimeError, "changed since approval"):
                apply_manifest(path, str(self.directory / "log.jsonl"), True, 25, 0)
            self.assertEqual(api.call_count, 1)


if __name__ == "__main__":
    unittest.main()
