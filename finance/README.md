# Finance Automation Control Center

**Less manual accounting work. Faster reviews. Clear records of what needs attention.**

Part of [Marketing OpenClaw AI](../README.md) · Built for OpenClaw AI agents · Created by **Tomas Corza** · [Portfolio](https://tomascorza.me)

The Finance Automation Control Center helps demonstrate how a business can use automation to check financial records, spot mistakes, and organize the work that needs an accountant's attention.

Instead of manually comparing every invoice, bank transaction, and employee timesheet, the system applies consistent checks and prepares a list of potential problems to review.

**What works today:** A runnable dashboard, Python validation tools, fictional sample records, downloadable reports, timekeeping checks, and bank-to-ledger matching suggestions. The code also includes a **Plaid bank-data API adapter** that can form part of a real bank connection.

**What is not connected yet:** Real bank accounts, QuickBooks, payroll, timeclock, and CRM services. The public dashboard uses fictional data. It does not send payments, change accounting records, or run a connected AI model.

## What can it do?

| Capability | What it does for a business |
| --- | --- |
| **Accounts receivable** | Shows how much customers owe, which invoices are overdue, and how long balances have been outstanding. Flags unusual payments and missing job references. |
| **Accounts payable** | Checks bills from suppliers, finds duplicate invoice numbers, and helps identify records that need attention before payment. |
| **Invoice matching** | Compares vendor bills with purchase orders, checking supplier names, PO numbers, and amounts. Highlights differences instead of approving a questionable bill. |
| **Bank reconciliation** | Compares bank transactions with bookkeeping entries to suggest matches and identify missing, duplicated, or unexpected transactions. |
| **QuickBooks Online payroll preparation** | Includes a read-only API client for permitted employee and time-activity records, plus a payroll-period review tool that works with separately supplied raw shift data. Does not approve, calculate, or submit payroll. |
| **Employee timekeeping** | Checks clock-in/out information, missing breaks, overlapping shifts, unusual hours, missing job IDs, and missing recorded supervisor approvals. |
| **Payroll preparation** | Creates a downloadable list of hours that passed the configured checks, ready for further payroll-team review. |
| **Job tracking** | Cross-checks job IDs on invoices and timesheets against a sample CRM/job list. |
| **Exception monitoring** | Creates an easy-to-review list explaining what went wrong, which record triggered it, and what an employee should check next. |
| **Reports and audit history** | Displays key figures and exceptions in a dashboard, with downloadable review reports and rule-decision records. |

These features run on the included **sample data**. Actual business data requires approved system connections and additional testing.

## How a bank account can be connected securely

A business does **not** need to give this automation unrestricted control of its money. The intended connection is **read-only**: the system can retrieve permitted transaction information so it can compare those transactions with accounting records, but it cannot initiate payments or transfers.

There are several possible ways to grant that access. **Which one is available depends on the bank, account type, and its security policies.**

### Option 1: A read-only banking API (preferred when supported)

Some banks provide business banking APIs or an approved third-party integration service with restricted permissions.

1. The business asks its bank whether it offers **read-only transaction access** through an API or approved data provider.
2. The bank or provider authorizes the connection and issues scoped credentials, such as a token or API key **if that institution supports them**.
3. The credentials are stored in a private, encrypted server-side secrets system—not in GitHub, an AI prompt, or the dashboard.
4. The integration retrieves transactions and passes them to the reconciliation tool.
5. The tool suggests matching bookkeeping entries and flags anything that needs human review.

**Important:** Not all banks issue a simple read-only API key. Many use OAuth, access tokens, customer consent, or an approved provider instead. Bank-specific API integration and credential storage still need to be configured.

### Option 2: A dedicated, read-only business banking user

Some business banking platforms let an administrator create another **named user** with limited access.

1. An authorized administrator creates a dedicated user in the bank's official business banking system, **if the bank supports restricted users**.
2. The administrator gives that user only the permissions needed to view transactions or download statements.
3. Payment initiation, transfers, beneficiary management, account administration, and approval permissions remain disabled.
4. Where supported, the integration uses the bank's **official API, OAuth/consent flow, or approved export mechanism** with this restricted identity.
5. Transactions are imported into the reconciliation workflow for review.

**A dedicated login is not automatically an API connection.** The application should **not** collect or store the banking username, password, or MFA codes, impersonate the user through browser automation, or bypass bank restrictions. If the bank only allows manual statement exports, an authorized employee can export a CSV for a future secure import workflow.

### Option 3: Connect through Plaid

The project already includes **server-side Plaid API methods** for a future bank integration.

1. The business opens an authorized **Plaid Link** connection screen.
2. The account holder selects their bank and completes the bank's required authorization steps.
3. Plaid gives the application's secure backend an access token for approved transaction-data access.
4. The backend retrieves available transactions and sends normalized records to the reconciliation engine.
5. The system suggests matching bookkeeping entries and holds unclear transactions for review.

Plaid is not the same as receiving a read-only API key directly from a bank. Its permissions depend on the authorized products, consent, bank support, and connection configuration.

**Current implementation status:** The project includes methods for creating Plaid Link tokens, exchanging public tokens, and retrieving transaction updates. A live Plaid Link screen, secure credential vault, persistent transaction sync, and a connection to an actual bank **have not yet been built or configured**. No account is currently connected.

[Read the technical bank connection guide](../docs/plaid-bank-reconciliation.md).

## What automatic reconciliation looks like

Imagine a business has the following fictional records:

| Bank activity | Bookkeeping entry | Result |
| --- | --- | --- |
| $425 supplier payment | $425 supplier payment on the same date/account | **Suggested match** |
| $1,200 customer deposit | $1,200 deposit on the same date/account | **Suggested match** |
| $72 payment | Two possible $72 entries | **Flag for review** |
| Pending $39 bank charge | No finalized entry | **Hold for review** |

The matching engine works conservatively. It proposes a match only when the mapped account, date, and amount agree and there is exactly **one** candidate on each side. It preserves source IDs and explains why other records were held.

An accountant still needs to verify proposed matches and confirm statement balances and period completeness. This does **not** automatically finalize a bank reconciliation inside QuickBooks or another accounting platform.

### The intended workflow

```text
Bank data (authorized read-only access)
                 +
Bookkeeping records (authorized access)
                 |
        Automatic comparison
                 |
         Suggested matches
            /         \
   Clear candidates   Missing / uncertain entries
            \         /
          Human review
                 |
      Approved accounting action
       (future integration only)
```

## QuickBooks Online payroll integration (assumed platform)

The project now contains a **read-only QuickBooks Online Accounting API adapter**. When an authorized business completes an Intuit OAuth 2.0 connection in a future secure deployment, the adapter can request permitted employee and time-activity records and summarize hours by employee and workday.

**Two data sources matter:** QuickBooks Online's `TimeActivity` records generally describe *durations*. They do not necessarily contain raw clock-in and clock-out events. For missed-punch detection, the business must additionally provide approved raw punches from its actual timeclock source, such as an appropriate QuickBooks Time/Workforce integration or export. The shift-checking module then flags missing endpoints and conflicting shifts.

The code also prepares a **review-only list of checked hours** for a selected pay period. It does not calculate tax-compliant pay, post hours to QuickBooks, authorize payroll, or initiate direct deposits. A payroll manager must complete the final review and run payroll through QuickBooks.

**Still needed for live use:** Intuit OAuth consent, secure token refresh/storage, verified API access, raw punch ingestion, integration testing, and an authenticated reviewer interface. Premium payroll API access is not assumed.

[QuickBooks Online connection and payroll design](../docs/quickbooks-online-payroll.md) · [Read-only adapter](quickbooks_online.py).

## How timekeeping works

The timekeeping tool reviews structured employee shift records and checks whether the recorded times make sense.

For example, it can flag a shift that overlaps another shift for the same employee, has no clock-out time, has an invalid break length, uses an unknown job number, or has no named recorded approval.

It can also generate a **CSV of recorded-approved hours that have no unresolved validation flags**, giving a payroll employee a starting point for review.

This is **not** a replacement for a payroll system. The tool does not calculate payroll taxes, employee deductions, wage compliance, or jurisdiction-specific overtime and meal/rest rules. Its break and long-shift flags are general review prompts, not legal determinations.

[View the timekeeping skill](../skills/timekeeping-review/SKILL.md).

## The dashboard

Run the finance demo locally from the repository's main folder:

```bash
python3 -m pip install -r dashboard/requirements.txt
streamlit run finance/dashboard.py
```

The dashboard shows:

- **Overview:** Outstanding receivables and payables, illustrative payroll, and exception counts.
- **Receivables, payables, and invoice matching:** Records, checks, and discrepancies.
- **Bank reconciliation and bank connection demo:** Sample bank records, suggested matches, and unmatched items.
- **Payroll and timekeeping:** Hours, shift checks, and an approved-hours review CSV.
- **CRM/jobs:** Sample jobs associated with financial and time records.
- **Exceptions, integrations, and audit log:** Review tasks, future connector information, and downloadable JSON reports.

The dashboard has a button to reveal the proposed finance work queue. It does not start a real banking sync or send financial instructions to another service.

## Run the local automation report

```bash
python3 -m finance.automation_runner --source synthetic --output-dir ./var/finance
```

This creates a local JSON summary and audit/run history based on the **original sample finance dataset**. It does not currently run the separate detailed bank reconciliation or shift-level timekeeping engines as part of this scheduled-style report. Live-source mode is intentionally disabled.

## What's ready and what still needs setup?

| Component | Status |
| --- | --- |
| Sample AR/AP and invoice checks | **Implemented** |
| Finance dashboard and sample reports | **Implemented** |
| Bank-to-ledger matching suggestions | **Implemented for structured records** |
| Plaid API client methods | **Implemented; not connected to a bank** |
| Timekeeping checks and reviewed-hours CSV | **Implemented for structured records** |
| Live bank authorization and transaction synchronization | **Requires secure setup and additional development** |
| Direct bank-issued API key support | **Bank-specific; not implemented as a general connector** |
| Dedicated bank user integration | **Bank-specific; not implemented** |
| QuickBooks Online read-only client | **API methods added; not connected** |
| QuickBooks, CRM, and payroll integrations | **Not connected** |
| Verified live approvals or automatic posting | **Not implemented** |

## What it takes to use this in a real business

A secure business deployment would involve identifying the accounting and banking systems already in use, securing **read-only access** where available, mapping accounts and transactions, protecting tokens and employee data, testing matching accuracy, and setting up employee approval and audit records.

The first production stage should compare records **without changing anything**. Only after successful testing and clear authorization should the business consider allowing narrowly controlled accounting updates.

## Project files

- [Finance dashboard](dashboard.py)
- [Accounts receivable, payable, and invoice validation](engine.py)
- [Bank reconciliation matching](bank_reconciliation.py)
- [Plaid connection adapter](plaid_connector.py)
- [Employee timekeeping](timekeeping.py)
- [QuickBooks Online read-only payroll review](quickbooks_online.py)
- [QuickBooks payroll integration guide](../docs/quickbooks-online-payroll.md)
- [Local automation runner](automation_runner.py)
- [Finance OpenClaw skill](../skills/finance-operations/SKILL.md)
- [Bank reconciliation OpenClaw skill](../skills/bank-reconciliation-review/SKILL.md)

---

**Built by Tomas Corza** · [Portfolio](https://tomascorza.me) · [Marketing OpenClaw AI on GitHub](https://github.com/Tomas-Corza/marketing-openclaw-ai)

*This is a public demonstration using fictional data. Actual banking, accounting, payroll, and CRM integrations require the organization's permission, secure configuration, and production testing.*
