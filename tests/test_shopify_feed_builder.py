import csv
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from tools.shopify_feed_builder import convert, save, shop_domain

HEADER = "Handle,Title,Body (HTML),Vendor,Variant SKU,Variant Price,Variant Inventory Tracker,Variant Inventory Qty,Variant Inventory Policy,Variant Barcode,Image Src,Option1 Value\n"
ROWS = (
    "lamp,Desk Lamp,<p>Task lighting</p>,Sample Lighting,LAMP-1,29.99,shopify,5,deny,012345678905,https://cdn.example.com/lamp.png,Small\n"
    "lamp,,,,LAMP-2,39.99,shopify,0,deny,012345678906,,Large\n"
    "chair,Chair,<p>Simple seating</p>,Example Furnishings,CHAIR-1,49.99,shopify,7,deny,000000000000,https://cdn.example.com/chair.png,Default Title\n"
)

class FeedBuilderTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.source=self.root/"products.csv"
        self.source.write_text(HEADER+ROWS)

    def test_variants_and_inventory(self):
        result=convert(str(self.source),"https://example.com")
        self.assertEqual(result["summary"]["accepted"],3)
        self.assertEqual(result["items"][0]["availability"],"in_stock")
        self.assertEqual(result["items"][1]["availability"],"out_of_stock")
        self.assertEqual(result["items"][1]["image_link"],"https://cdn.example.com/lamp.png")
        self.assertEqual(result["items"][0]["item_group_id"],"lamp")

    def test_tsv_and_rss_output(self):
        result=convert(str(self.source),"https://example.com")
        for fmt in ("tsv","rss"):
            out=self.root/("feed."+fmt)
            rejects=self.root/("rejects-"+fmt+".json")
            save(result,str(out),str(rejects),fmt,"https://example.com")
            self.assertTrue(out.exists())
            self.assertEqual(json.loads(rejects.read_text())["summary"]["accepted"],3)
            if fmt=="tsv":
                with out.open(newline="") as f:
                    data=list(csv.DictReader(f,delimiter="\t"))
                self.assertEqual(data[0]["price"],"29.99 USD")
            else:
                root=ET.parse(out).getroot()
                self.assertEqual(len(root.findall("./channel/item")),3)

    def test_untracked_excluded_without_explicit_assertion(self):
        self.source.write_text(HEADER+"lamp,Desk Lamp,<p>Task lighting</p>,Vendor,LAMP,29.99,,,,,https://cdn.example.com/lamp.png,\n")
        result=convert(str(self.source),"https://example.com")
        self.assertEqual(result["summary"]["accepted"],0)
        self.assertEqual(result["summary"]["rejected"],1)
        approved=convert(str(self.source),"https://example.com",allow_untracked=True)
        self.assertEqual(approved["summary"]["accepted"],1)

    def test_duplicate_ids_rejected(self):
        self.source.write_text(HEADER+ROWS+ROWS.splitlines(keepends=True)[0])
        result=convert(str(self.source),"https://example.com")
        self.assertEqual(result["summary"]["rejected"],1)

    def test_reject_invalid_price(self):
        self.source.write_text(HEADER+"lamp,Lamp,<p>Lamp</p>,Vendor,LAMP,not-a-price,shopify,2,deny,,https://cdn.example.com/lamp.png,\n")
        result=convert(str(self.source),"https://example.com")
        self.assertEqual(result["summary"]["accepted"],0)

    def test_url_must_be_https_root(self):
        for url in ("http://example.com","https://example.com/shop","https://user:pass@example.com","https://example.com?x=y"):
            with self.assertRaises(ValueError):
                shop_domain(url)

if __name__=="__main__":
    unittest.main()
