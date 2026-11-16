import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tools.shopify_ai_copy import extract_response_text, generate_copy, run, source_record

class AICopyTests(unittest.TestCase):
    def test_source_fields_only(self):
        record = source_record({"handle":"lamp","title":"Desk Lamp","email":"secret@example.com","descriptionHtml":"<p>Bright</p>"})
        self.assertNotIn("email", record)
        self.assertEqual(record["existing_description"],"Bright")

    def test_extract_output(self):
        self.assertEqual(extract_response_text({"output":[{"type":"message","content":[{"type":"output_text","text":"hello"}]}]}),"hello")

    @patch("tools.shopify_ai_copy.urllib.request.urlopen")
    def test_html_is_escaped(self, mock_urlopen):
        draft={"product_title":"Lamp","description_text":"Light <script>alert(1)</script>","seo_title":"Lamp","seo_description":"Lighting","jtbd_angle":"Task lighting hypothesis","review_notes":"Check facts"}
        class Resp:
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def read(self): return json.dumps({"status":"completed","output":[{"type":"message","content":[{"type":"output_text","text":json.dumps(draft)}]}]}).encode()
        mock_urlopen.return_value=Resp()
        output=generate_copy({"title":"Lamp"},"gpt-4.1-mini","fake-key")
        self.assertIn("&lt;script&gt;",output["suggested_changes"]["descriptionHtml"])
        self.assertNotIn("<script>",output["suggested_changes"]["descriptionHtml"])

    @patch("tools.shopify_ai_copy.generate_copy")
    def test_batch_draft_unapproved(self, gen):
        gen.return_value={"suggested_changes":{"title":"Lamp","descriptionHtml":"<p>Lamp</p>","seo":{"title":"Lamp","description":"Lighting"}},"jtbd_hypothesis":"Lighting","review_notes":"Review"}
        with tempfile.TemporaryDirectory() as temp:
            csv=Path(temp)/"catalog.csv"
            out=Path(temp)/"report.json"
            csv.write_text("Handle,Title,Body (HTML)\nlamp,Lamp,<p>Lighting</p>\n")
            result=run(str(csv),str(out),"gpt-4.1-mini",10,0,"fake-key")
            self.assertEqual(result["drafts_created"],1)
            item=json.loads(out.read_text())["items"][0]
            self.assertIs(item["approved"],False)
            self.assertIs(item["publishable"],False)

    def test_requires_key(self):
        with self.assertRaisesRegex(RuntimeError,"OPENAI_API_KEY"):
            run("unused.csv","unused.json","model",10,0,"")

if __name__=="__main__":
    unittest.main()
