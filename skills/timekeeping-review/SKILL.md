---
name: timekeeping-review
description: Validate time entries and prepare review-only, approved hours for downstream payroll integrations; synthetic examples by default.
---

# Timekeeping and payroll preparation

Built for OpenClaw AI agents. This skill analyzes structured time-entry records using `finance.timekeeping.analyze_shifts`.

## Workflow
1. Obtain a **separately authorized** and access-controlled timesheet export or use `demo_shifts()` for a public demonstration.
2. Validate unique shift IDs, employee and CRM job IDs, clock-in/out timestamps (with timezone offsets), breaks, overlaps, long days, and named supervisor approvals.
3. Route exceptions to a human reviewer. Never silently fix, discard, or alter a source time entry.
4. Release only exception-free approved **hours** to a download-ready review artifact. Keep source records and rule decisions available for audit.
5. Obtain payroll-team signoff, validate jurisdiction-specific overtime and break rules in the payroll system, and reconcile against source data before any actual payroll import.

## Run
```bash
python3 -m unittest discover -s tests -p 'test_timekeeping.py' -v
streamlit run finance/dashboard.py
```

## Safety boundaries
- **No live timeclock, HRIS, payroll, QuickBooks or CRM connector** is included.
- This is not an overtime, wage, meal/rest compliance, or payroll-tax calculator. The example break rule is a review heuristic, not a California compliance assessment.
- Never modify recorded hours, infer approval, send employee data to an AI model, or submit payroll autonomously.
- Restrict live employee data by role, encrypt in transit and at rest, establish retention and access logs, and confirm applicable labor requirements with qualified payroll/HR professionals.
