import tempfile
import unittest
from pathlib import Path

from tools.shopify_live_feed_sync import graphql_pages, variant_row, run

def node(ident="123"):
    return {
        "legacyResourceId": ident, "sku": "SKU-1", "barcode": "012345678905",
        "price": "29.99", "inventoryQuantity": 5, "inventoryPolicy": "DENY",
        "availableForSale": True, "inventoryItem": {"tracked": True},
        "selectedOptions": [{"name":"Title","value":"Default Title"}],
        "image": {"url": "https://cdn.example.com/item.jpg"},
        "product": {
            "handle": "lamp", "title": "Lamp", "descriptionHtml": "<p>Good lamp</p>",
            "vendor": "Example", "status": "ACTIVE",
            "onlineStoreUrl": "https://example.com/products/lamp",
            "featuredImage": {"url": "https://cdn.example.com/item.jpg"},
        },
    }

class LiveFeedTests(unittest.TestCase):
    def test_pagination(self):
        calls = []
        def fetch(query, variables):
            calls.append(variables["after"])
            return {"productVariants": {
                "nodes": [node(str(len(calls)))],
                "pageInfo": {"hasNextPage": len(calls)<2,
                             "endCursor": "next"+str(len(calls))},
            }}
        result=list(graphql_pages(fetch=fetch))
        self.assertEqual(len(result),2)
        self.assertEqual(calls,[None,"next1"])

    def test_variant_mapping_and_publish_filter(self):
        self.assertEqual(variant_row(node())["Variant SKU"],"shopify-variant-123")
        hidden=node()
        hidden["product"]["onlineStoreUrl"]=None
        self.assertIsNone(variant_row(hidden))

    def test_stale_cursor_rejected(self):
        def fetch(query, variables):
            return {"productVariants": {"nodes": [],
                "pageInfo": {"hasNextPage": True, "endCursor": "same"}}}
        with self.assertRaisesRegex(RuntimeError,"repeated pagination cursor"):
            list(graphql_pages(fetch=fetch))

    def test_offline_generate_feed(self):
        def fetch(query, variables):
            return {"productVariants": {"nodes": [node()],
                "pageInfo": {"hasNextPage": False, "endCursor": None}}}
        with tempfile.TemporaryDirectory() as temp:
            out=str(Path(temp)/"feed.xml")
            report=str(Path(temp)/"rejections.json")
            results=run(out,report,"https://example.com","USD","rss",False,True,fetch)
            self.assertEqual(results["accepted"],1)
            self.assertTrue(Path(out).exists())

    def test_no_valid_items_aborts(self):
        hidden=node()
        hidden["product"]["onlineStoreUrl"]=None
        def fetch(query,variables):
            return {"productVariants": {"nodes":[hidden],
                "pageInfo":{"hasNextPage":False,"endCursor":None}}}
        with tempfile.TemporaryDirectory() as temp:
            out=str(Path(temp)/"feed.xml")
            with self.assertRaisesRegex(RuntimeError,"No valid"):
                run(out,str(Path(temp)/"rejected.json"),"https://example.com","USD","rss",False,True,fetch)
            self.assertFalse(Path(out).exists())

if __name__=="__main__":
    unittest.main()
