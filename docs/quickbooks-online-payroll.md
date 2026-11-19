# QuickBooks Online Payroll Integration — current capabilities

This module is designed to help a business reduce manual time review **without letting an AI agent pay employees or modify their accounting system**.

## What has been added

- A read-only QuickBooks Online Accounting API client for permitted **Employee** and **TimeActivity** records.
- A time-activity summary grouped by employee and date, with malformed or duplicate record flags.
- A payroll-period preparation function that reuses the existing shift-level review rules (missing punch/end time, overlap, break validity, job mapping, named approval indicator).
- Clear exceptions and a review-only hours artifact; **no payroll run or direct deposit**.
- Offline unit tests. These tests are not a live QuickBooks integration test.

## How a business would connect QuickBooks Online

1. Register an Intuit developer application for the company and select the required supported Accounting API permissions.
2. Have an authorized QuickBooks company administrator approve the integration through Intuit's **OAuth 2.0** sign-in and consent process.
3. Store the granted access/refresh tokens **encrypted on a secure backend** associated with the correct QuickBooks company `realm_id`. Never ask staff to disclose QuickBooks passwords to OpenClaw.
4. Configure a token refresh process and permission-limited service, then pass the active access token into the read-only `QBOReadOnlyClient`.
5. Verify employee identifiers and TimeActivity records; separately connect the company's actual timeclock source if the goal is to identify missed clock-in/out punches.
6. Run a parallel trial against payroll managers' approved payroll reports before using the review output to inform the next pay period.

**The OAuth consent UI, token refresh/storage, secure backend and live connection have not been implemented in this repository.**

### Code example (requires an independently obtained, authorized token)

```python
from finance.quickbooks_online import QBOReadOnlyClient, summarize_qbo_time_activities

client = QBOReadOnlyClient(realm_id="1234567890", access_token=secure_access_token)
employees = client.employees()
activities = client.time_activities()
review = summarize_qbo_time_activities(activities)
# Present review to authorized staff, do not auto-submit payroll.
```

## What QuickBooks integration does *not* guarantee

- A **TimeActivity** record is a duration record, not guaranteed raw clock-in and clock-out events. To identify a missed punch, use approved clock-event exports or QuickBooks Time/Workforce source features with sufficient access.
- Standard QuickBooks Online Accounting API access does not grant general permission to calculate wages or send direct deposits.
- Premium payroll/compensation API access may depend on Intuit's partner program and approved API scopes. Do not assume a TimeActivity entry appears as approved payroll time.
- Any future automated payroll submission requires supported provider endpoints, explicit authenticated approval, reliable idempotency, and full compliance review. **This code deliberately has no payment or payroll-write methods.**

## Offline test

```bash
python3 -m unittest discover -s tests -p 'test_quickbooks_online.py' -v
```

## Business outcome

OpenClaw can gather time information and turn missing or conflicting records into a short review list before a payroll deadline. QuickBooks remains the system that calculates and processes the employees' actual payroll after a responsible person approves it.
