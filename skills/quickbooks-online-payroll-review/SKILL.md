---
name: quickbooks-online-payroll-review
description: Read-only QuickBooks Online employee/time-activity review and approval-gated payroll preparation. No payroll execution or payments.
---

# QuickBooks Online Payroll Preparation

**Built for OpenClaw AI agents.** The adapter in `finance.quickbooks_online` provides *read-only* QuickBooks Online Accounting API access to Employee and TimeActivity records using a separately authorized OAuth access token. It does **not** initiate or approve payroll.

## What to do

1. Use an already authenticated, authorized server session and configured Intuit OAuth credentials. Do **not** request or store passwords, OAuth client secrets, access tokens, tax numbers, salary, or banking information in an AI prompt.
2. Retrieve permitted employees and TimeActivity records using `QBOReadOnlyClient.employees()` and `time_activities()`; obey rate limits and tenant isolation.
3. Call `summarize_qbo_time_activities()` to group recorded durations by employee/date and identify missing or malformed references.
4. **Do not assume TimeActivity records contain raw punches or supervisor approvals.** If QuickBooks Time or another approved punch source is available, normalize those raw start/end entries and pass them to `prepare_payroll_review()` for missing-punch, overlap, break, job, and approval checks.
5. Present the exception report and reviewed-hours artifact to the authorized payroll manager. Reconcile source records, approved hours, payroll provider output and bank debits after the payroll provider runs payroll.
6. Human staff must calculate/verify applicable wages, overtime, paid breaks, leave, withholding and deductions in their payroll system and explicitly authorize the payroll run.

## Non-negotiable restrictions

- No payroll creation, payroll submission, direct deposits or payments.
- No mutations to QuickBooks employees, timesheets or ledger.
- No inference of approval from the mere existence of time records.
- No production use of unvalidated sample data, cached credentials, or personal information in the public dashboard.
- Standard QuickBooks Online Accounting API access does not automatically include premium Payroll Compensation APIs; check Intuit partner access before planning a pay-type integration.
- Live OAuth onboarding, token refresh, secure storage, payroll-provider write access and QuickBooks Time punch ingestion are **not implemented**.

## Local validation

```bash
python3 -m unittest discover -s tests -p 'test_quickbooks_online.py' -v
```

See [finance documentation](../../finance/README.md).
