"""Tests for deterministic, auditable, customer-level rule-based attribution."""
import unittest
from tools.multi_touch_attribution import attribute

T = [
    {"touchpoint_id": "t1", "customer_id": "a", "channel": "Search", "occurred_at": "2026-01-01T00:00:00Z"},
    {"touchpoint_id": "t2", "customer_id": "a", "channel": "Email", "occurred_at": "2026-01-03T00:00:00+00:00"},
    {"touchpoint_id": "t3", "customer_id": "a", "channel": "Social", "occurred_at": "2026-01-05T00:00:00Z"},
]
C = [{"conversion_id": "o1", "customer_id": "a", "converted_at": "2026-01-06T00:00:00Z", "revenue": "100.00"}]


class AttributionTests(unittest.TestCase):
    def test_linear_revenue_conserved_despite_rounding(self):
        result = attribute(T, C)
        self.assertEqual([r["attributed_revenue"] for r in result["allocations"]], ["33.34", "33.33", "33.33"])
        self.assertEqual(result["totals"]["attributed_revenue"], "100.00")
        self.assertAlmostEqual(sum(x["weight"] for x in result["allocations"]), 1)

    def test_first_and_last_touch(self):
        for model, expected in [("first_touch", "t1"), ("last_touch", "t3")]:
            with self.subTest(model=model):
                rows = attribute(T, C, model=model)["allocations"]
                winner = next(row for row in rows if row["attributed_revenue"] == "100.00")
                self.assertEqual(winner["touchpoint_id"], expected)

    def test_position_based(self):
        rows = attribute(T, C, model="position_based")["allocations"]
        self.assertEqual([r["attributed_revenue"] for r in rows], ["40.00", "20.00", "40.00"])

    def test_time_decay_prioritizes_recent_touches(self):
        rows = attribute(T, C, model="time_decay", half_life_days=2)["allocations"]
        amounts = [float(row["attributed_revenue"]) for row in rows]
        self.assertLess(amounts[0], amounts[1])
        self.assertLess(amounts[1], amounts[2])
        self.assertEqual(sum(amounts), 100)

    def test_excludes_future_outside_window_and_other_people(self):
        extra = T + [
            {"touchpoint_id": "future", "customer_id": "a", "channel": "Search", "occurred_at": "2026-01-07T00:00:00Z"},
            {"touchpoint_id": "old", "customer_id": "a", "channel": "Search", "occurred_at": "2025-01-01T00:00:00Z"},
            {"touchpoint_id": "other", "customer_id": "b", "channel": "Search", "occurred_at": "2026-01-04T00:00:00Z"},
        ]
        ids = [r["touchpoint_id"] for r in attribute(extra, C)["allocations"]]
        self.assertEqual(ids, ["t1", "t2", "t3"])

    def test_unattributed_kept_visible_not_invented(self):
        conv = C + [{"conversion_id": "o2", "customer_id": "unknown", "converted_at": "2026-01-06T00:00:00Z", "revenue": "20.00"}]
        totals = attribute(T, conv)["totals"]
        self.assertEqual(totals["unattributed_conversions"], 1)
        self.assertEqual(totals["unattributed_revenue"], "20.00")
        self.assertEqual(totals["attributed_revenue"], "100.00")

    def test_rejects_missing_timezone_duplicates_bad_revenue(self):
        bad = [dict(T[0], occurred_at="2026-01-01T00:00:00")]
        with self.assertRaises(ValueError):
            attribute(bad, C)
        with self.assertRaises(ValueError):
            attribute(T + [T[0]], C)
        with self.assertRaises(ValueError):
            attribute(T, [dict(C[0], revenue="-1")])
        with self.assertRaises(ValueError):
            attribute(T, [dict(C[0], revenue="0.001")])
        with self.assertRaises(ValueError):
            attribute(T, C + C)

    def test_one_and_two_touches_position_based(self):
        for n in (1, 2):
            result = attribute(T[:n], C, model="position_based")
            self.assertEqual(sum(float(r["attributed_revenue"]) for r in result["allocations"]), 100)


if __name__ == "__main__":
    unittest.main()
