"""Test synthetic-only interactive attribution adapters without Streamlit."""
import unittest
from dashboard.attribution_view import MODELS, comparison_rows, fixture_rows, run_demo, EVENTS, ORDERS


class AttributionDashboardTests(unittest.TestCase):
    def test_fixture_is_synthetic(self):
        events = fixture_rows(EVENTS)
        orders = fixture_rows(ORDERS)
        self.assertGreater(len(events), 0)
        self.assertGreater(len(orders), 0)
        self.assertTrue(all(row["order_id"].startswith("demo-") for row in orders))
        self.assertTrue(all(row["user_pseudo_id"].startswith("synthetic-") for row in events))

    def test_demo_matches_orders_without_inventing_credit(self):
        result = run_demo("linear", 30, 7)
        self.assertEqual(result["pipeline_audit"]["total_shopify_orders"], 8)
        self.assertEqual(result["pipeline_audit"]["ga4_matched_orders"], 7)
        self.assertEqual(result["pipeline_audit"]["attributed_orders"], 7)
        self.assertEqual(result["pipeline_audit"]["orders_without_verified_purchase_match"], 1)
        self.assertEqual(result["totals"]["attributed_revenue"], "1318.69")

    def test_all_models_preserve_total_eligible_revenue(self):
        for model in MODELS.values():
            with self.subTest(model=model):
                result = run_demo(model, 30, 7)
                self.assertEqual(result["totals"]["attributed_revenue"], "1318.69")

    def test_short_lookback_removes_old_touchpoints(self):
        result = run_demo("linear", 1, 7)
        self.assertEqual(result["pipeline_audit"]["matched_orders_without_eligible_touchpoints"], 3)
        self.assertEqual(result["totals"]["attributed_revenue"], "743.49")

    def test_all_seven_channels_appear(self):
        result = run_demo("linear", 30, 7)
        self.assertEqual({row["channel"] for row in result["channels"]}, {
            "Meta Ads", "Google Ads", "Microsoft Ads (Bing)", "Etsy Referral",
            "Amazon Referral", "ChatGPT Referral", "Google Organic",
        })

    def test_model_comparison_has_separate_channels(self):
        rows = comparison_rows(30, 7)
        self.assertTrue(rows)
        self.assertEqual(set(x["Attribution model"] for x in rows), set(MODELS))
        self.assertTrue(all(x["Attributed revenue (USD)"] >= 0 for x in rows))


if __name__ == "__main__":
    unittest.main()
