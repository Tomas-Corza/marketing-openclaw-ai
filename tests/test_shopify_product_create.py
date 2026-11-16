"""Offline tests for reviewed Shopify DRAFT creation; no external Shopify calls."""
import unittest
from unittest.mock import patch

from tools.shopify_product_create import (
    CREATE_MUTATION, create_draft, draft_preview, validated_media, validated_product,
)

SPEC = {
    "title": "Architectural Pendant",
    "descriptionHtml": "<p>Verified sample fixture description</p>",
    "vendor": "Example Lighting",
    "productType": "Pendant",
    "seo": {"title": "Architectural Pendant"},
    "images": [{"url": "https://example.com/image.jpg", "alt": "Pendant fixture"}],
}


class DraftCreateTests(unittest.TestCase):
    def test_preview_always_draft(self):
        preview = draft_preview(SPEC)
        self.assertEqual(preview["product"]["status"], "DRAFT")
        self.assertEqual(preview["media"][0]["mediaContentType"], "IMAGE")
        self.assertEqual(len(preview["input_sha256"]), 64)
        self.assertFalse(preview["created"])
        self.assertIn("productCreate", CREATE_MUTATION)

    def test_reject_unapproved_or_changed_content_without_api(self):
        sha = draft_preview(SPEC)["input_sha256"]
        with patch("tools.shopify_product_create.shopify_graphql") as api:
            with self.assertRaises(ValueError):
                create_draft(SPEC, sha, confirmed=False)
            with self.assertRaises(ValueError):
                create_draft({**SPEC, "title": "Different"}, sha, confirmed=True)
            api.assert_not_called()

    def test_success_calls_shopify_once_with_draft(self):
        sha = draft_preview(SPEC)["input_sha256"]
        with patch("tools.shopify_product_create.shopify_graphql") as api:
            api.return_value = {"productCreate": {"product": {"id": "gid://shopify/Product/123", "title": SPEC["title"], "status": "DRAFT"}, "userErrors": []}}
            result = create_draft(SPEC, sha, confirmed=True)
            self.assertTrue(result["created"])
            self.assertFalse(result["published"])
            api.assert_called_once()
            product = api.call_args.args[1]["product"]
            self.assertEqual(product["status"], "DRAFT")
            self.assertEqual(product["title"], SPEC["title"])

    def test_shopify_errors_and_missing_id(self):
        sha = draft_preview(SPEC)["input_sha256"]
        for result in [
            {"productCreate": {"userErrors": [{"message": "Access denied"}]}},
            {"productCreate": {"product": None, "userErrors": []}},
            {"productCreate": {"product": {"id": "gid://shopify/Product/123", "status": "ACTIVE"}, "userErrors": []}},
        ]:
            with patch("tools.shopify_product_create.shopify_graphql", return_value=result):
                with self.assertRaises(RuntimeError):
                    create_draft(SPEC, sha, confirmed=True)

    def test_disallows_unsafe_fields_and_bad_images(self):
        for field, value in [("status", "ACTIVE"), ("price", "1"), ("inventory", 3), ("variants", [])]:
            with self.assertRaises(ValueError):
                validated_product({**SPEC, field: value})
        with self.assertRaises(ValueError):
            validated_product({"title": ""})
        with self.assertRaises(ValueError):
            validated_media({"images": [{"url": "http://example.com/image.jpg"}]})
        with self.assertRaises(ValueError):
            validated_media({"images": [{"url": "https://user:pass@example.com/image.jpg"}]})


if __name__ == "__main__":
    unittest.main()
