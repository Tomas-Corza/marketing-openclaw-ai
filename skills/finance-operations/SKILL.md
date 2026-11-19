---
name: finance-operations
description: Review-first accounting automation checks on synthetic or authorized offline records, including invoice matching, AP, AR, reconciliation, payroll time validation, and exception monitoring.
---

# Finance Operations (synthetic demo)

This is an additional OpenClaw skill, not a production accounting connector.

## Capabilities
- Compare vendor bills against purchase orders; detect duplicate invoice identifiers
- Summarize AR open balances and aging; propose collections follow-ups
- Match bank transactions and ledger entries by account, reference, and amount
- Flag unapproved hours and missing CRM job identifiers
- Produce a review queue, audit events and a local Streamlit dashboard

## Run locally
From the project root:
```bash
python3 -m unittest discover -s tests -p 'test_finance_engine.py' -v
python3 -m pip install -r dashboard/requirements.txt
streamlit run finance/dashboard.py
```

## Execution restrictions
Never claim the demo connects to QuickBooks, Salesforce, bank accounts, or payroll providers. It does not.
Do not transmit, approve or pay invoices, alter financial records, initiate payroll, or auto-reconcile accounting records.
Do not input real financial information into a public Streamlit deployment.
No LLM agent or live webhook is wired to this skill; the work queue is rules-based.
For production work, require the owner's authorization, scoped credentials, retention rules, independent reconciliation and human approvals.
