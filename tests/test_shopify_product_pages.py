"""Offline tests: no Shopify credentials or store access required."""
import json
import tempfile
import unittest
from pathlib import Path

from tools.shopify_product_pages import audit, load_proposal, product_gid


class ShopifyProductPagesTests(unittest.TestCase):
    def test_numeric_product_id(self):
        self.assertEqual(product_gid("123"), "gid://shopify/Product/123")

    def test_invalid_product_id_rejected(self):
        with self.assertRaises(ValueError):
            product_gid("https://untrusted.example/product")

    def test_audit_missing_content(self):
        result = audit({
            "id": "gid://shopify/Product/123",
            "title": "Demo",
            "descriptionHtml": "<p>Short text</p>",
            "seo": {"title": "", "description": ""},
        })
        self.assertEqual(len(result["findings"]), 3)

    def test_proposal_rejects_unauthorized_fields(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "proposal.json"
            p.write_text(json.dumps({"price": "0.01"}))
            with self.assertRaises(ValueError):
                load_proposal(str(p))

    def test_proposal_accepts_content_fields(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "proposal.json"
            p.write_text(json.dumps({"seo": {"title": "Verified example"}}))
            self.assertEqual(load_proposal(str(p))["seo"]["title"], "Verified example")


if __name__ == "__main__":
    unittest.main()
