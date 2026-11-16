"""Offline tests for CSV-to-Shopify draft imports."""
import csv
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tools.shopify_bulk_product_create import COLUMNS, build_products, create_one, preview, start_import

BASE = {"handle": "example-pendant", "title": "Example Pendant",
        "description_html": "<p>Verified sample</p>", "vendor": "Example Lighting",
        "product_type": "Pendant", "seo_title": "Example Pendant",
        "seo_description": "Example", "option1_name": "Finish",
        "option1_value": "Black", "sku": "PENDANT-BLACK", "price": "120.00"}

def csv_bytes(rows):
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=COLUMNS, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: row.get(key, "") for key in COLUMNS})
    return out.getvalue().encode()

class BulkImportTests(unittest.TestCase):
    def test_groups_two_variants(self):
        second = {**BASE, "option1_value": "White", "sku": "PENDANT-WHITE", "price": "129.50"}
        result = preview(csv_bytes([BASE, second]))
        self.assertEqual(result["product_count"], 1)
        self.assertEqual(result["variant_count"], 2)
        product = result["products"][0]
        self.assertEqual(product["status"], "DRAFT")
        self.assertEqual(product["variants"][1]["price"], "129.50")
        self.assertEqual(product["productOptions"][0]["name"], "Finish")

    def test_rejects_invalid_rows(self):
        bad_rows = [
            [{**BASE, "sku": ""}],
            [BASE, {**BASE, "sku": "PENDANT-BLACK", "option1_value": "White"}],
            [BASE, {**BASE, "sku": "SECOND", "option1_value": "Black"}],
            [{**BASE, "price": "-1.00"}],
            [{**BASE, "price": "12.999"}],
            [{**BASE, "option1_value": ""}],
            [{**BASE, "title": ""}],
            [BASE, {**BASE, "sku": "SECOND", "title": "Inconsistent", "option1_value": "Blue"}],
        ]
        for rows in bad_rows:
            with self.subTest(rows=rows):
                with self.assertRaises(ValueError):
                    build_products(csv_bytes(rows))

    def test_approval_required_before_api_calls(self):
        source = csv_bytes([BASE])
        with tempfile.TemporaryDirectory() as folder:
            log = Path(folder) / "journal.jsonl"
            with patch("tools.shopify_bulk_product_create.shopify_graphql") as api:
                with self.assertRaises(ValueError):
                    start_import(source, "incorrect", True, log)
                with self.assertRaises(ValueError):
                    start_import(source, preview(source)["input_sha256"], False, log)
                self.assertFalse(log.exists())
                api.assert_not_called()

    def test_creates_unpublished_and_secure_journal(self):
        source = csv_bytes([BASE])
        with tempfile.TemporaryDirectory() as folder:
            log = Path(folder) / "journal.jsonl"
            with patch("tools.shopify_bulk_product_create.shopify_graphql") as api:
                api.side_effect = [
                    {"products": {"nodes": []}},
                    {"productSet": {"product": {"id": "gid://shopify/Product/123", "status": "DRAFT", "handle": "example-pendant"}, "userErrors": []}},
                ]
                result = start_import(source, preview(source)["input_sha256"], True, log)
            self.assertEqual(result["count"], 1)
            self.assertFalse(result["published"])
            self.assertEqual(log.stat().st_mode & 0o777, 0o600)
            self.assertIn('"event": "created"', log.read_text())
            with self.assertRaises(FileExistsError):
                start_import(source, preview(source)["input_sha256"], True, log)

    def test_duplicate_handle_blocks_creation(self):
        item = build_products(csv_bytes([BASE]))[0]
        with patch("tools.shopify_bulk_product_create.shopify_graphql",
                   return_value={"products": {"nodes": [{"handle": "example-pendant", "id": "gid://shopify/Product/123"}]}}) as api:
            with self.assertRaisesRegex(ValueError, "already contains"):
                create_one(item)
            api.assert_called_once()

    def test_partial_failure_stops_and_records(self):
        second = {**BASE, "handle": "example-sconce", "title": "Example Sconce", "sku": "SCONCE-1"}
        source = csv_bytes([BASE, second])
        with tempfile.TemporaryDirectory() as folder:
            log = Path(folder) / "journal.jsonl"
            with patch("tools.shopify_bulk_product_create.shopify_graphql") as api:
                api.side_effect = [
                    {"products": {"nodes": []}},
                    {"productSet": {"product": {"id": "gid://shopify/Product/1", "status": "DRAFT"}, "userErrors": []}},
                    {"products": {"nodes": []}},
                    RuntimeError("network timeout"),
                ]
                with self.assertRaisesRegex(RuntimeError, "Stopped at example-sconce"):
                    start_import(source, preview(source)["input_sha256"], True, log)
            self.assertIn('"event": "created"', log.read_text())
            self.assertIn('"event": "stopped"', log.read_text())

if __name__ == "__main__":
    unittest.main()
