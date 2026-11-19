# Finance Automation Control Center

**Review-first financial operations automation, built for OpenClaw AI agents.**

Part of [Marketing OpenClaw AI](../README.md) · Developed by **Tomas Corza** · [Portfolio](https://tomascorza.me)

The Finance Automation Control Center is a modular Python prototype that demonstrates how a business can standardize accounting checks, identify discrepancies, and prepare evidence-backed review queues across receivables, payables, bank reconciliation, job tracking, and employee timekeeping.

> **Current status:** Runnable, **synthetic-data-only** dashboard and deterministic Python analysis tools, plus an **optional server-side Plaid API client** that requires separate authorization and infrastructure. This is **not** a live bank, QuickBooks, CRM, or payroll deployment; it does not execute financial writes or model-driven AI decisions.

## What the system actually does

| Business workflow | Implemented capability | Output / boundary |
| --- | --- | --- |
| **Accounts receivable (AR)** | Calculates open balances from billed-minus-paid amounts, groups them by due-date aging (current, 1–30, 31–60, 61–90, 90+ days), flags payments exceeding invoices and balances overdue more than 30 days, and checks CRM job references | AR totals, aging chart, exceptions, proposed collections follow-up **draft task**; does not contact customers |
| **Accounts payable (AP)** | Reviews vendor bills, detects duplicate vendor/invoice identifiers, excludes such duplicates from the illustrative AP outstanding total, and cross-checks purchase-order links | Outstanding AP estimate and flagged duplicate/mismatched invoices; no bill approval or payment |
| **Invoice-to-purchase-order matching** | Matches invoice PO reference, vendor identity, and exact amount against the sample PO list; flags missing POs, vendor mismatches, and amount variances | Explainable matching audit and suggested manual investigation; no OCR, three-way receipt matching, or posting |
| **Bank reconciliation (original finance view)** | Compares fictional bank and ledger entries by account, reference, and amount; flags unmatched, ambiguous, or discrepant entries | Proposed reconciliation checks; not a completed bank statement reconciliation |
| **Bank-to-ledger reconciliation (new module)** | Normalizes Plaid transaction sign convention, maps bank account IDs to ledger accounts, and proposes one-to-one matches with **exact mapped account, posting date, and amount**; holds pending, duplicate, unmapped, malformed, missing-counterpart, and ambiguous entries | Proposed matches with source transaction/ledger IDs and review-only exceptions; never marks entries reconciled |
| **Optional Plaid bank-data adapter** | Includes server-side methods for Link-token creation, public-token exchange, and paginated transaction change retrieval through Plaid | API integration building blocks; **not** a working user-facing bank connection, encrypted token vault, transaction database, or automatically connected dashboard |
| **Basic payroll and time checks** | Compares fictional employee-entered hours with approved hours, checks associated job IDs, and computes a simple illustrative straight-time gross-pay total | Flags hours beyond approved amounts and unknown job IDs; **not** production payroll calculation |
| **Shift-level timekeeping** | Validates time-zone-aware clock-in/out times, shift identifiers, employee IDs, CRM job IDs, break durations, missing named approvals, overlapping shifts, and unusually long shifts/days | Exception reports, audit decisions, and CSV containing only exception-free, recorded-approved hours; no timeclock integration or actual supervisor approval |
| **CRM / job visibility** | Displays fictional customer/job records and validates their IDs when referenced in AR and time workflows | Missing job reference flags; no CRM API connection |
| **Exception monitoring** | Assigns reason, severity, source record, and recommended human action for deterministic finance-engine exceptions; provides a proposed work queue | Review-only recommendations, not agent-executed resolutions |
| **Reporting & scheduled-style runs** | Provides Streamlit tables/charts, audit JSON downloads, and a Python command-line validation runner | Local JSON snapshot and run log for synthetic finance-engine checks; no live-source scheduler or automated external notifications |

### What is automated vs. what requires a person

```text
Fictional records / separately authorized future data adapters
                      |
           Deterministic validation
                      |
       Matching + discrepancy detection
                      |
          Proposed match / exception
                      |
              Human review
                      |
       Reporting and review-only exports
```

The code **does** calculate summaries, detect predefined anomalies, generate proposed matches, and build review artifacts. It **does not** automatically authorize or post invoices, update the general ledger, initiate payments, send collections emails, reconcile bank accounts in accounting software, modify timesheets, or submit payroll.

The label *built for OpenClaw AI agents* refers to the framework's modular skills and integration architecture. **The finance implementation currently uses deterministic Python rules, not a connected large-language-model agent.**

## Explore the dashboard

Run from the repository root:

```bash
python3 -m pip install -r dashboard/requirements.txt
streamlit run finance/dashboard.py
```

The dashboard includes **12 tabs**:

1. **Overview** — AR/AP/payroll illustration, aging and exception distribution.
2. **Accounts Receivable** — customer invoice balances and aging.
3. **Accounts Payable** — vendor bill records and outstanding amount.
4. **Invoice Matching** — PO reference verification and discrepancy review.
5. **Bank Reconciliation** — original fictional bank-versus-ledger comparison.
6. **Bank Connection Demo** — separate synthetic Plaid-style reconciliation example; proposed matches, exceptions, JSON download.
7. **Payroll & Time** — hours, approval-hour mismatches, straight-time illustration.
8. **Timekeeping Review** — synthetic shift checks, audit results and approved-hours **review CSV**.
9. **CRM / Jobs** — illustrative job links.
10. **Exceptions & Agent Queue** — rule-triggered issues and suggested actions.
11. **Integrations** — readiness notes, not active connection status.
12. **Audit Log** — validation decisions and finance-engine JSON download.

**Dashboard behavior:** The initial data is generated locally, and the `Run finance validation` button enables display of the proposed task queue. The tab analyses are based on deterministic processing of fictional data; the button does not launch an external AI agent or a remote job.

## Bank connection: precise implementation status

**Implemented code:** [`plaid_connector.py`](plaid_connector.py) provides a configurable Plaid sandbox/development/production HTTP client with methods to:

- Request a Link token for an authenticated user ID.
- Exchange an authorized Link public token for an access token and item ID.
- Retrieve paginated added, modified, and removed transaction events and return a next cursor.

**Not implemented:** Plaid Link frontend, authenticated deployment endpoints, credential encryption/storage, per-customer access separation, durable transaction sync/cursor persistence, webhook handling, live ledger adapter, account mapping UI, scheduled bank sync, and signed-off posting. **No bank account is connected in the demonstration.** The dashboard never asks for account credentials.

The separate [`bank_reconciliation.py`](bank_reconciliation.py) engine can process appropriately normalized bank and ledger records supplied by an authorized backend. It is deliberately conservative: a single exact-date, exact-amount match is a *proposal*, not proof that a transaction is properly reconciled or classified. It does not verify statement opening/closing balances, posting-date tolerances, fees, currency differences, or settled-period completeness.

See [Bank connection and security deployment guide](../docs/plaid-bank-reconciliation.md).

## Timekeeping and payroll-preparation details

[The timekeeping engine](timekeeping.py) currently accepts structured shift records rather than raw timeclock API responses. It checks:

- Timestamp presence and UTC offsets; chronological start/end and break-duration validity.
- Missing/duplicate shift IDs and missing employee identifiers.
- Job ID association with a provided CRM job list.
- Named approval markers in the input data.
- Overlapping intervals for the same employee.
- Review heuristics for shifts longer than 16 hours, daily recorded hours over 12, and shifts of 6+ elapsed hours with no recorded break.

These are **review heuristics only** and do not encode California or other jurisdiction's overtime, meal/rest, prevailing-wage, or labor-compliance requirements. The engine computes recorded hours after entered break minutes; it does **not** determine which breaks are paid or unpaid. Hours lacking any required review check are excluded from its approved-hours CSV.

A named approval value in fictional input data is not verified authentication or proof of actual supervisor authorization. The downloaded CSV is **for payroll-team review**, not direct payroll submission.

See [OpenClaw timekeeping skill](../skills/timekeeping-review/SKILL.md).

## Running a local finance validation report

```bash
python3 -m finance.automation_runner --source synthetic --output-dir ./var/finance
```

This command executes the **original finance-engine synthetic checks**, then writes:

- `var/finance/latest.json` — latest finance summary, exceptions, audit records and suggested review tasks.
- `var/finance/runs.jsonl` — local run metadata and output hash.

It uses a file lock and restrictive local output permissions. It does **not** currently include the separate bank-reconciliation and shift-level timekeeping modules in its scheduled snapshot. Passing `--source live` is intentionally rejected until a production adapter is developed. Scheduling is a deployment step; the command is not itself an always-on service.

## Offline usage and tests

```bash
python3 -m unittest discover -s tests -p 'test_finance_engine.py' -v
python3 -m unittest discover -s tests -p 'test_timekeeping.py' -v
python3 -m unittest discover -s tests -p 'test_bank_reconciliation.py' -v
```

Tests are included in the repository. **Do not interpret their presence as proof of production readiness; the new bank and timekeeping tests have not yet been verified in this session.**

The bank reconciliation module can also be used independently:

```python
from finance.bank_reconciliation import synthetic_example, reconcile

bank, ledger, account_mapping = synthetic_example()
review = reconcile(bank, ledger, account_mapping)
print(review["summary"])
print(review["exceptions"])
```

## Implementation status by system

| System | Current status |
| --- | --- |
| Built-in synthetic accounting dataset | **Implemented** |
| Streamlit finance dashboard | **Implemented** (synthetic demonstration) |
| AR/AP, invoice matching and finance-engine checks | **Implemented** (offline deterministic rules) |
| Timekeeping checks and reviewed-hours CSV | **Implemented** (structured fictional records) |
| Bank-to-ledger proposed matching | **Implemented** (structured records) |
| Plaid API client methods | **Implemented as backend building blocks**; authorization UI and live operational flow are not connected |
| QuickBooks Online integration | **Not implemented** |
| Bank account actually linked in the dashboard | **Not implemented** |
| CRM / job platform integration | **Not implemented** |
| Timeclock / HRIS / payroll provider integration | **Not implemented** |
| Authenticated supervisor approvals, persisted exceptions | **Not implemented** |
| Automated accounting or payroll writes | **Not implemented; intentionally blocked** |
| LLM-powered finance agent execution | **Not implemented** |

## Production deployment requirements

Before a business can safely use real financial or employee records, implementation would require documented authorization, isolated server-side credentials, role-based permissions, encrypted storage, persistent transaction cursors, secure data ingestion, idempotent matching, audit retention, reviewer identity and signoff, independent reconciliation, payroll compliance review, logging/alerts, and controlled integration testing.

A production workflow should begin **read-only** and run in parallel with existing accounting procedures before any narrowly authorized write operation is considered.

## Files and OpenClaw integration

| File | Purpose |
| --- | --- |
| [`dashboard.py`](dashboard.py) | Unified Streamlit finance prototype |
| [`engine.py`](engine.py) | AR/AP/PO/ledger/time synthetic analysis and review queue |
| [`bank_reconciliation.py`](bank_reconciliation.py) | Strict bank-to-ledger proposed matches and exceptions |
| [`plaid_connector.py`](plaid_connector.py) | Optional Plaid server-side API client |
| [`timekeeping.py`](timekeeping.py) | Shift-level time validation and reviewed-hours selection |
| [`automation_runner.py`](automation_runner.py) | Local finance-engine report generation |
| [Finance operations skill](../skills/finance-operations/SKILL.md) | OpenClaw usage and execution boundaries |
| [Bank reconciliation skill](../skills/bank-reconciliation-review/SKILL.md) | Review-only reconciliation workflow |
| [Timekeeping skill](../skills/timekeeping-review/SKILL.md) | Review-only timekeeping workflow |

---

**Created by Tomas Corza** · [Portfolio](https://tomascorza.me) · [Full GitHub repository](https://github.com/Tomas-Corza/marketing-openclaw-ai)

*This repository is a public, synthetic demonstration of practical financial workflow automation. All financial and employee records in the included examples are fictional. Actual integrations, legal compliance, accounting controls and deployment security depend on the specific business environment.*
