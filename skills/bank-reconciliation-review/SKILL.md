---
name: bank-reconciliation-review
description: Prepare read-only bank-to-ledger reconciliation proposals using fictional records or separately authorized Plaid transaction exports; never post automatically.
---

# Bank Reconciliation Review

This OpenClaw agent skill operates using `finance.bank_reconciliation`. Optional Plaid backend plumbing is in `finance.plaid_connector` and requires an authorized secure deployment.

## Procedure

1. Use `synthetic_example()` for public demonstrations. Do not request bank passwords or paste bank access tokens into agent context.
2. For a private authorized implementation, obtain normalized, posted transactions through an authenticated bank-data backend. Never put Plaid credentials in prompts or public dashboards.
3. Independently retrieve authorized accounting ledger records, then explicitly map banking accounts to ledger accounts.
4. Run `reconcile(bank_transactions, ledger_entries, account_mapping)`.
5. Present `proposed_matches`, `exceptions`, and `audit` for a human reviewer. Preserve original source IDs and any approval notes separately.
6. Do not modify accounting entries, mark anything reconciled, move money, or automatically accept suggestions.

## Limits

This prototype uses exact mapped account/date/amount checks only; it does not establish statement coverage, guarantee correct accounting classification, or validate bank balances. Bank-connection authorization UI, encrypted token storage, durable transaction sync and accounting ledger API integration are **future deployment work**. See [deployment architecture](../../docs/plaid-bank-reconciliation.md).
