# Read-only bank connection and reconciliation (Plaid)

Marketing OpenClaw AI includes a **server-side Plaid adapter** and deterministic, approval-first reconciliation tool. Its **dashboard currently demonstrates the process using fictional records**. There is no deployed Plaid Link UI, bank connection, credential vault, persisted cursor, accounting API write, or automatic bank-to-ledger import.

## Why Plaid

A customer connects their own institution using **Plaid Link**, not by giving the application online banking credentials. The application receives a short-lived `public_token`, exchanges it **on the server** for an `access_token`, and requests transaction data with a minimum-privilege `transactions` scope. Bank availability and institution support vary.

## Deployment sequence

1. Register an approved Plaid application and configure its environment and secure authentication controls.
2. Set `PLAID_CLIENT_ID`, `PLAID_SECRET` and `PLAID_ENV=sandbox` as server-side secrets. Never place these or returned access tokens in Git, browser JavaScript, public dashboards or logs.
3. From an authenticated backend, call `PlaidBankClient().create_link_token(authenticated_user_id)`; provide the returned Link token to an authorized Plaid Link frontend (not included).
4. After the user completes Link, exchange the short-lived public token via `exchange_public_token(public_token)`; store the access token encrypted per authorized tenant in a credential vault (not implemented here).
5. Call `sync_transactions(access_token, prior_cursor)`. Apply *all* added/modified/removed events to an encrypted per-tenant transaction store and commit the new cursor only after a successful atomic application. A storage layer, retry and paging recovery must be implemented before production use.
6. Export or pull the matching accounting ledger from an independently authorized accounting integration (not implemented). Normalize bank and ledger account mappings, transaction dates and signs. Call `reconcile(bank_rows, ledger_rows, account_mapping)`.
7. Show proposed matches and exceptions to authorized accounting reviewers. The engine **never posts, clears, accepts, or edits a transaction**. Obtain signoff and perform independent reconciliation against statement balances and closing dates before posting via any future accounting adapter.

### Example: fictional offline reconciliation

```python
from finance.bank_reconciliation import synthetic_example, reconcile
bank, ledger, account_map = synthetic_example()
review = reconcile(bank, ledger, account_map)
print(review["summary"])
```

### Example: server-side API adapter initialization

```python
from finance.plaid_connector import PlaidBankClient
client = PlaidBankClient()  # reads environment secrets
link_token = client.create_link_token("authenticated-internal-user-id")
# A separately implemented, authenticated frontend opens Plaid Link.
# After Link returns a public_token to the backend:
# item = client.exchange_public_token(public_token)
# Never print or commit item["access_token"].
```

## Reconciliation rules

- Plaid positive transaction amounts indicate outflow and negative amounts indicate inflow. The reconciliation tool inverts the sign to compare with ledger conventions.
- Proposed matches require **one unique posted bank record and one unique ledger entry** with matching mapped account, ISO date and exact amount.
- Pending transactions, malformed records, duplicate IDs, missing mappings, and one-to-many or many-to-one ambiguities are held for human review.
- Dates from Plaid and the ledger may differ due to posting delays; this conservative prototype will **not** silently match those records. Production adapters need explicit date-tolerance policies and supporting evidence.
- Deleted/modified transactions returned by sync must replace the prior local records; reconciliation must not use obsolete or duplicated copies.
- Records and approval decisions require auditable retention, immutable review history, role-based permissions and tenant isolation. These controls are architecture requirements, **not implemented persistence** in this module.

## Security and limitations

- The example Streamlit dashboard does not connect to live bank accounts, and intentionally provides no field for bank login credentials or access tokens.
- No OAuth vault, signed webhook validation, Link UI, persistent cursor database, secure multi-user session management, or live accounting-system adapter is included.
- The adapter makes **read-only transaction retrieval requests** and exchanges authorized Plaid tokens. It cannot initiate ACH transfers or move money.
- Never use personal, employee, customer, or business financial data in a public synthetic demo. Live financial data should be processed only in a secured private deployment with access controls, encryption, approved retention, audit logging and incident-response plans.
- Before production, test pagination and sync mutation recovery, consent/disconnection, duplicate accounting entries, statement coverage, balance discrepancies, chargebacks, fees, currency and time-zone differences, and bank/provider downtime.

## Test the offline reconciliation engine

```bash
python3 -m unittest discover -s tests -p 'test_bank_reconciliation.py' -v
streamlit run finance/dashboard.py
```
