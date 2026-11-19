# Finance Automation Control Center

**Less manual accounting work. Faster reviews. Clear records of what needs attention.**

Part of [Marketing OpenClaw AI](../README.md) · Built for OpenClaw AI agents · Created by **Tomas Corza** · [Portfolio](https://tomascorza.me)

The Finance Automation Control Center helps demonstrate how a business can use automation to check financial records, spot mistakes, and organize the work that needs an accountant's attention.

Instead of manually comparing every invoice, bank transaction, and employee timesheet, the system applies consistent checks and prepares a list of potential problems to review.

## Connect it to the systems your business already uses

The Finance Automation Control Center is designed to work alongside your existing business software. With the company's permission and a secure connection, it can bring information from different systems together, check for discrepancies, and show employees what needs attention.

- **Business bank accounts:** Connect through an approved, read-only bank service such as Plaid, a bank-supported connection, or authorized statement exports. Compare deposits and withdrawals with bookkeeping records to find transactions that may be missing or duplicated.
- **QuickBooks Online:** Connect with the company's authorization to review available employee time records and, with additional accounting integration, compare invoices, expenses, and payroll-related transactions. Payroll remains under the control of authorized staff.
- **Employee time clocks and timesheets:** Connect an approved timekeeping system or export to check for missing clock-ins or clock-outs, overlapping shifts, unusual hours, and timesheets that need supervisor review.
- **Payroll systems:** Prepare verified hours for an authorized payroll manager to review before employees are paid through the company's payroll provider.
- **Customer and job management software:** Connect job, customer, and purchase-order information so invoices, expenses, and employee hours can be checked against the correct projects.

**How connections work:** An authorized company representative approves access through the service's supported connection method. Wherever possible, the system uses **view-only permission**, meaning it can read the information needed for checks without making payments or changing records. Available connections depend on the software and its permissions.

**Demonstration and deployment:** The public dashboard uses fictional business records to show these workflows. Live connections require secure setup, the company's authorization, and testing before the automation can work with actual financial or employee information.

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

## QuickBooks Online: employee time and payroll review

**Assumed setup:** QuickBooks Online for Sivan-style financial operations. This is a proposed integration—not a connection to Sivan's account.

The project now includes a **read-only QuickBooks Online client** that is designed to retrieve permitted employee and time records through Intuit's official API. It can make payroll preparation easier by organizing recorded hours, identifying incomplete records, and sending exceptions to a manager.

### What the QuickBooks code can do today

| Function | What happens |
| --- | --- |
| **Retrieve employee records** | The `QBOReadOnlyClient.employees()` method requests permitted employee records from QuickBooks Online when provided with an authorized access token and company ID. |
| **Retrieve recorded time** | `time_activities()` requests QuickBooks `TimeActivity` entries. These entries contain time durations, not necessarily individual clock-in and clock-out events. |
| **Summarize hours** | `summarize_qbo_time_activities()` groups valid entries by employee and date and flags duplicate IDs, missing employee references, or invalid durations. |
| **Review a pay period** | `prepare_payroll_review()` accepts separately supplied, structured clock-in/out shifts, applies timekeeping checks, and returns exception-free, recorded-approved hours within the chosen pay period for a manager to review. |
| **Explain exceptions** | The review result identifies missing clock-outs, conflicting shifts, problematic breaks, unknown job IDs, and incomplete approval markers when those issues appear in the supplied raw shift records. |

**Important:** The client and review methods are implemented in Python, but **the full QuickBooks sign-in/authorization process has not been implemented**, and no company has been connected. The Streamlit dashboard continues to display fictional sample data.

### How a business would connect QuickBooks Online

1. An authorized company administrator approves an Intuit app using **QuickBooks Online OAuth 2.0**, selecting the permissions that the integration actually needs.
2. A secure backend stores the QuickBooks company ID and access/refresh tokens. **No one should give OpenClaw their QuickBooks password or paste tokens into an AI prompt.**
3. With the granted API permissions, the read-only adapter retrieves employee and time-activity records.
4. The company also connects its actual timeclock records, if available, through a supported QuickBooks Time/Workforce integration or approved export. **A duration-only time entry cannot reliably prove that a punch is missing.**
5. OpenClaw's deterministic checks prepare a list of incomplete records and reviewed hours for the payroll manager.
6. The manager checks payroll rules, overtime, paid/unpaid breaks, leave, employee classifications, and totals, then **runs payroll inside QuickBooks**.
7. Once a future bank/ledger connection is securely configured, the reconciliation module could compare the resulting payroll-related bank transactions with accounting entries and flag discrepancies for review.

### Example: missed clock-out

An employee clocks in at 8:00 AM, but the source timeclock record has **no clock-out timestamp**. The timekeeping engine flags that entry as incomplete and holds it out of the reviewed-hours export. A supervisor must check the actual record and correct it in the authorized timekeeping system; the agent does **not** invent an end time or silently adjust the employee's pay.

### What this does *not* do

- It **does not calculate wages, taxes, benefits, overtime pay, or legally compliant meal/rest entitlements**.
- It **does not update QuickBooks timesheets**, approve payroll, run payroll, or initiate direct deposit.
- It **does not access raw clock punches** from QuickBooks Online's `TimeActivity` API alone.
- It **does not automatically reconcile live payroll payments** because the real bank and accounting feeds are not connected.
- It **does not include a production OAuth screen, token vault, automatic token refresh, or authenticated payroll manager approval interface**.

The standard QuickBooks Online Accounting API should not be assumed to provide unrestricted access to payroll processing. Available payroll APIs and permissions depend on Intuit products and partner eligibility.

**Related files:** [QuickBooks Online read-only client](quickbooks_online.py) · [Payroll integration guide](../docs/quickbooks-online-payroll.md) · [OpenClaw payroll review skill](../skills/quickbooks-online-payroll-review/SKILL.md) · [Unit tests](../tests/test_quickbooks_online.py).

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

This creates a local JSON summary and audit/run history based on the **original sample finance dataset**. It does not currently run the separate detailed bank reconciliation, shift-level timekeeping, or QuickBooks review modules as part of this scheduled-style report. Live-source mode is intentionally disabled.

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
| QuickBooks Online employee/time-activity API client | **Read-only code added; requires authorized OAuth setup** |
| QuickBooks pay-period reviewed-hours function | **Implemented for separately provided shift records; not submitted to payroll** |
| QuickBooks, CRM, and payroll integrations | **No live accounts connected** |
| Payroll payments / direct deposits | **Not implemented — payroll manager uses QuickBooks** |
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
- [QuickBooks OpenClaw payroll review skill](../skills/quickbooks-online-payroll-review/SKILL.md)
- [Local automation runner](automation_runner.py)
- [Finance OpenClaw skill](../skills/finance-operations/SKILL.md)
- [Bank reconciliation OpenClaw skill](../skills/bank-reconciliation-review/SKILL.md)

---

**Built by Tomas Corza** · [Portfolio](https://tomascorza.me) · [Marketing OpenClaw AI on GitHub](https://github.com/Tomas-Corza/marketing-openclaw-ai)

*This is a public demonstration using fictional data. Actual banking, accounting, payroll, and CRM integrations require the organization's permission, secure configuration, and production testing.*
