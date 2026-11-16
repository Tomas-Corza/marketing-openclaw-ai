"""Offline Streamlit dashboard business-logic tests; no Streamlit or credentials required."""
from pathlib import Path
import unittest

from dashboard.logic import (
    approval_manifest, ensure_size, json_bytes, locally_reviewed_preview,
    parse_catalog, parse_feed, queue_change, read_optional_json,
    run_diagnostics, source_fingerprint, summarize, tsv_bytes,
)

ROOT = Path(__file__).resolve().parents[1] / "examples" / "dashboard"


class OperationsDashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = parse_catalog((ROOT / "shopify_catalog.csv").read_bytes())
        cls.items = parse_feed((ROOT / "merchant_feed.tsv").read_bytes(), "merchant_feed.tsv")
        cls.merchant = read_optional_json((ROOT / "merchant_status.json").read_bytes(), "products")
        cls.drafts = read_optional_json((ROOT / "ai_drafts.json").read_bytes(), "items")

    def test_demo_data_and_shopify_reuse(self):
        self.assertEqual(self.catalog["products_scanned"], 4)
        self.assertEqual(len(self.items), 4)
        self.assertGreater(len(self.catalog["drafts"]), 0)

    def test_merchant_diagnostics_integration(self):
        report = run_diagnostics(self.items, self.merchant)
        self.assertEqual(report["merchant_disapproved_products"], 1)
        self.assertIn("invalid_image_link", {x["code"] for x in report["issues"]})
        summary = summarize(self.catalog, report, self.drafts)
        self.assertEqual(summary["ai_drafts"], 2)
        self.assertGreater(summary["critical_issues"], 0)

    def test_source_hash_changes_when_data_changes(self):
        self.assertNotEqual(source_fingerprint(b"catalog", b"feed"),
                            source_fingerprint(b"catalog", b"feed2"))

    def test_local_feed_edit_requires_explicit_approval(self):
        changes = queue_change(self.items, {}, "LAMP-001", "title", "Verified lamp name")
        original = self.items[0]["title"]
        manifest = approval_manifest(self.items, changes, set())
        self.assertIs(manifest[0]["approved"], False)
        with self.assertRaises(ValueError):
            locally_reviewed_preview(self.items, manifest)
        manifest = approval_manifest(self.items, changes, {"LAMP-001"})
        result = locally_reviewed_preview(self.items, manifest)
        self.assertEqual(result[0]["title"], "Verified lamp name")
        self.assertEqual(self.items[0]["title"], original)
        self.assertIn(b"Verified lamp name", tsv_bytes(result))
        self.assertIn(b'"approved": true', json_bytes(manifest))

    def test_cannot_edit_price_availability_or_unknown_ids(self):
        with self.assertRaises(ValueError):
            queue_change(self.items, {}, "LAMP-001", "price", "0.01 USD")
        with self.assertRaises(ValueError):
            queue_change(self.items, {}, "LAMP-001", "availability", "in_stock")
        with self.assertRaises(ValueError):
            queue_change(self.items, {}, "not-found", "title", "Title")
        with self.assertRaises(ValueError):
            queue_change(self.items, {}, "LAMP-001", "title", "   ")

    def test_stale_source_blocks_preview(self):
        changes = queue_change(self.items, {}, "LAMP-001", "title", "Verified name")
        manifest = approval_manifest(self.items, changes, {"LAMP-001"})
        changed_items = [dict(row) for row in self.items]
        changed_items[0]["price"] = "999.99 USD"
        with self.assertRaisesRegex(ValueError, "changed since approval"):
            locally_reviewed_preview(changed_items, manifest)

    def test_upload_guards(self):
        with self.assertRaises(ValueError):
            ensure_size(b"")
        with self.assertRaises(ValueError):
            ensure_size(b"x" * 5_000_001)
        with self.assertRaises(ValueError):
            read_optional_json(b'{"wrong": []}', "products")
        with self.assertRaises(ValueError):
            parse_feed(b"not a feed", "feed.tsv")


if __name__ == "__main__":
    unittest.main()
