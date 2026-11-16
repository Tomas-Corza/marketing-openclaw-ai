import json
import unittest
from tools.merchant_feed_ai_triage import triage

class AITriageTests(unittest.TestCase):
    def test_requires_key(self):
        with self.assertRaises(ValueError):
            triage({"issues": []},"","gpt-4.1-mini")

    def test_no_issues_skips_api(self):
        result=triage({"issues": []},"test","gpt-4.1-mini")
        self.assertEqual(result["recommendations"],[])

    def test_rejects_nonexistent_issue(self):
        draft={"summary":"review","recommendations":[{"offer_id":"fake","issue_code":"fake",
               "priority":"high","action":"verify","verification":"check source"}]}
        class Response:
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def read(self): return json.dumps({"status":"completed","output":[{"type":"message",
                "content":[{"type":"output_text","text":json.dumps(draft)}]}]}).encode()
        def opener(req, timeout): return Response()
        report={"issues":[{"offer_id":"sku","code":"invalid_price",
                          "priority":"critical","message":"Invalid price","field":"price"}]}
        with self.assertRaisesRegex(ValueError,"absent from input"):
            triage(report,"test","gpt-4.1-mini",opener=opener)

if __name__=="__main__":
    unittest.main()
