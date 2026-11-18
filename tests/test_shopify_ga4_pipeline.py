import unittest
from tools.shopify_ga4_pipeline import prepare

def event(eid,uid="browser1",name="page_view",when="2026-01-02T00:00:00Z",channel="Paid Search",tx="",consent="Yes"):
    return {"event_id":eid,"user_pseudo_id":uid,"event_name":name,"occurred_at":when,
            "channel":channel,"transaction_id":tx,"analytics_storage":consent}

def order(oid="1001",revenue="99.99",currency="USD"):
    return {"order_id":oid,"converted_at":"2026-01-04T00:00:00Z","revenue":revenue,"currency":currency}

class ShopifyGA4Tests(unittest.TestCase):
    def test_order_matching_and_credit(self):
        e=[event("a"),event("b",channel="Email",when="2026-01-03T00:00:00Z"),
           event("p",name="purchase",when="2026-01-04T00:00:00Z",tx="1001")]
        r=prepare(e,[order()])
        self.assertEqual(r["pipeline_audit"]["ga4_matched_orders"],1)
        self.assertEqual(r["totals"]["attributed_revenue"],"99.99")
        self.assertEqual({x["channel"] for x in r["allocations"]},{"Paid Search","Email"})
    def test_unmatched_purchase_is_not_linked(self):
        r=prepare([event("a"),event("p",name="purchase",tx="wrong")],[order()])
        self.assertEqual(r["pipeline_audit"]["ga4_matched_orders"],0)
        self.assertEqual(r["totals"]["attributed_revenue"],"0.00")
    def test_denied_consent(self):
        e=[event("a",consent="No"),event("p",name="purchase",tx="1001",consent="No")]
        self.assertEqual(prepare(e,[order()])["pipeline_audit"]["ga4_matched_orders"],0)
    def test_ambiguous_purchase_ids(self):
        e=[event("p",name="purchase",tx="1001"),event("p2",uid="browser2",name="purchase",tx="1001")]
        r=prepare(e,[order()])
        self.assertEqual(r["pipeline_audit"]["ambiguous_order_count"],1)
        self.assertEqual(r["totals"]["attributed_revenue"],"0.00")
    def test_future_and_direct_excluded(self):
        e=[event("a"),event("direct",channel="Direct"),
           event("future",when="2026-01-05T00:00:00Z"),
           event("p",name="purchase",when="2026-01-04T00:00:00Z",tx="1001")]
        self.assertEqual([x["touchpoint_id"] for x in prepare(e,[order()])["allocations"]],["a"])
    def test_mixed_currencies_rejected(self):
        with self.assertRaises(ValueError):
            prepare([],[order(),order("1002",currency="EUR")])
    def test_duplicates_rejected(self):
        with self.assertRaises(ValueError):
            prepare([event("a"),event("a")],[order()])
        with self.assertRaises(ValueError):
            prepare([],[order(),order()])
    def test_purchase_without_touch_is_unattributed(self):
        r=prepare([event("p",name="purchase",tx="1001")],[order()])
        self.assertEqual(r["pipeline_audit"]["matched_orders_without_eligible_touchpoints"],1)
        self.assertEqual(r["totals"]["unattributed_conversions"],1)

if __name__ == "__main__":
    unittest.main()
