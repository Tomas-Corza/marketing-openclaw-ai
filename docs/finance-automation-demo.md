# Finance Automation Control Center — synthetic interview demo

A separate Streamlit accounting operations prototype inside Marketing OpenClaw AI. It is a **rules-based demonstration**, not an existing QuickBooks integration or an autonomous AI agent.

## Run
```bash
python3 -m pip install -r dashboard/requirements.txt
streamlit run finance/dashboard.py
```
Or deploy `finance/dashboard.py` as the Streamlit Community Cloud entrypoint; use only the included fictional records.

## What is implemented
- AR aging and outstanding balances
- AP vendor invoice list and duplicate detection
- Invoice-to-PO matching (vendor, reference and total), proposed manual verification
- Bank-to-ledger transaction matching, mismatch and unmatched-entry detection
- Payroll/time sheet exception checks and illustrative gross-pay estimate
- CRM job cross-reference
- Rules-based review queue, audit log and downloadable JSON
- Integration-readiness view outlining proposed QuickBooks, CRM, banking, payroll, webhook and automation-platform connections

## What is not implemented
- Actual QuickBooks, Salesforce, bank-feed, payroll, n8n, Make or Zapier connectors
- Invoice OCR, actual AI/LLM reasoning, automatic ingestion or asynchronous job execution
- Posting journals, payments, invoices or payroll; approving financial transactions
- Reconciliation across multiple currencies, ambiguous identifiers, partial payments, complex tax rules or real overtime calculations

## Production design
1. Confirm the organization's financial systems, chart-of-accounts mapping, permission model and data protection requirements.
2. Add approved OAuth2/read-only integrations to a secure server, not the public dashboard.
3. Normalize vendor/customer identifiers, date/time zones, currency and precise decimal amounts.
4. Implement idempotent event ingestion with webhook verification, deduplication, retries and immutable audit logs.
5. Preserve human signoff on bills, journals, exceptions, payroll and disbursements.
6. Run parallel to existing accounting processes with documented reconciliation, alerts and recovery procedures before authorizing any production writes.

## Portfolio wording
“Built a synthetic finance-operations prototype extending Marketing OpenClaw AI. Demonstrates deterministic AP invoice checks, AR aging, bank reconciliation exceptions, timesheet review, and an approval-first audit queue. Live accounting APIs and AI execution are future integration phases.”
