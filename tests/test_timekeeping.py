"""Offline tests for synthetic timekeeping, approval gating and exception handling."""
import unittest
from finance.timekeeping import analyze_shifts, demo_shifts


class TestTimekeeping(unittest.TestCase):
    def setUp(self):
        self.jobs = {"JOB-1042", "JOB-1043", "JOB-1044"}

    def test_demo_flags_and_holds(self):
        result = analyze_shifts(demo_shifts(), self.jobs)
        rules = {x["rule"] for x in result["exceptions"]}
        self.assertTrue({"overlapping_shift", "approval_required", "unknown_job", "invalid_shift", "missing_break"} <= rules)
        self.assertEqual([x["shift_id"] for x in result["payroll_ready"]], ["SHIFT-005"])
        self.assertEqual(result["summary"]["approved_hours_ready"], 8.0)

    def test_duplicate_ids_block_both(self):
        shifts = [dict(demo_shifts()[-1]), dict(demo_shifts()[-1])]
        self.assertEqual(analyze_shifts(shifts, self.jobs)["payroll_ready"], [])

    def test_missing_approver_blocks_export(self):
        shift = dict(demo_shifts()[-1], approver="")
        result = analyze_shifts([shift], self.jobs)
        self.assertEqual(len(result["payroll_ready"]), 0)

    def test_negative_break_blocks_export(self):
        shift = dict(demo_shifts()[-1], break_minutes=-10)
        result = analyze_shifts([shift], self.jobs)
        self.assertEqual(len(result["payroll_ready"]), 0)

    def test_invalid_timezone_blocks_export(self):
        shift = dict(demo_shifts()[-1], start="2026-11-17T08:00:00")
        result = analyze_shifts([shift], self.jobs)
        self.assertEqual(len(result["payroll_ready"]), 0)


if __name__ == "__main__":
    unittest.main()
