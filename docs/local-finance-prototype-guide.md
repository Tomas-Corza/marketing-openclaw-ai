# Local finance prototype: setup, verification, demo and limits

This guide explains the **working synthetic-only finance prototype** included in Marketing OpenClaw AI. It does **not** require financial API keys or a running OpenClaw agent.

## Verified implementation

| Component | What exists today |
| --- | --- |
| Rule-based engine | Fictional AR/AP aging, purchase order matching, bank-to-ledger comparison, timesheet exceptions and CRM job references |
| Streamlit dashboard | Local interactive view over seeded synthetic data (`finance/dashboard.py`) |
| Batch runner | Independent CLI execution using the same engine (`finance/automation_runner.py`) |
| Generated output | `var/finance/latest.json` and `var/finance/runs.jsonl` |
| Concurrency/safety | Single-run lock, atomic latest report replacement, local file permissions, no financial writes |
| Scheduler | Optional cron-compatible launcher (`scripts/run_finance_cron.sh`); **no schedule installed by cloning** |
| Tests | `tests/test_finance_runner.py` and finance engine tests |

The dashboard is **not yet wired to display the CLI runner's `latest.json` report**. It renders its own synthetic dataset on each session. The runner rejects `--source live`.

## First-time install on macOS

Prerequisites: Git, Python 3.10+, network access to clone the repository.

```bash
cd ~
git clone https://github.com/Tomas-Corza/marketing-openclaw-ai.git
cd marketing-openclaw-ai
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r dashboard/requirements.txt
```

Existing local copy:

```bash
cd ~/marketing-openclaw-ai
git switch main
git pull origin main
source .venv/bin/activate
```

Optional OpenClaw CLI/Gateway setup is a **separate step**. These finance scripts work without it.

## Test the independent Python runner

```bash
python -m finance.automation_runner --source synthetic
python -m unittest discover -s tests -p 'test_finance_runner.py' -v
ls -la var/finance
python -m json.tool var/finance/latest.json
tail -n 5 var/finance/runs.jsonl
```

Expected: JSON success response with `source: synthetic`, two runner tests passing, and local reports. Exception count is fixture-dependent, not a real business metric.

The output directory `var/` is gitignored. Do not upload operational or confidential data to GitHub.

## Run and present the dashboard

```bash
streamlit run finance/dashboard.py
```

Open the **Local URL printed by Streamlit** (commonly `localhost:8501` or `localhost:8502`). If another service already uses a port, the number may differ. Press **Control+C** in that Terminal to stop the server.

Suggested five-minute walkthrough: accounts receivable and payable → invoice/PO matching → bank/ledger exceptions → timesheet checks → exceptions and review queue → independent batch runner and JSON audit output.

Click **Run finance validation** to show a review-only proposed work queue. State plainly that all records are fictional and that the current processing is **deterministic Python**, not live AI inference. No vendor payments, payroll submissions, accounting journal postings or bank edits are performed.

The dashboard uses the current Streamlit `width="stretch"` argument rather than deprecated `use_container_width=True` (PR #28). Any optional Watchdog suggestion is not a blocker.

## Scheduling is optional, not a product default

The repository contains a **launcher**, not an automatic weekday schedule. The user removed the temporary 8 AM cron example from the local prototype after testing it. Scheduling decisions must depend on each business use case and the availability/freshness of incoming data.

Manual launcher test from the repo root:

```bash
OPENCLAW_REPO="$PWD" PYTHON_BIN="$PWD/.venv/bin/python" sh scripts/run_finance_cron.sh
```

Review user-level cron configuration with `crontab -l`. A blank result means no jobs are configured for that user. Do not type a cron schedule directly into the shell. For optional examples see [finance scheduling](finance-scheduling-setup.md). On a laptop, cron jobs may not run while asleep; a reliable production deployment needs an always-available scheduler and monitoring.

## Future integration boundaries

- **Banking:** approved read-only API/feed, institution/provider consent, transaction identifiers and reconciliation policy.
- **QuickBooks:** authorized OAuth connection, scoped permissions, verified schema/account mapping.
- **CRM and payroll:** provider-specific APIs, stable IDs, data minimization and supervisor review.
- **Secrets:** approved runtime secret retrieval, such as Bitwarden Secrets Manager machine identity; never embed credentials in Git, public Streamlit apps or cron commands.
- **LLM providers:** add vetted calls for descriptions, extraction or suggested actions after validation; financial amounts and approval decisions remain deterministic/human-controlled.
- **Operational orchestration:** configuration-driven schedules, webhooks, retry/idempotency guarantees, alerting, access management, retention controls and integration testing remain **planned**, not implemented.

Adding a credential does **not** automatically enable an integration. Live accounts require adapter development, authorization, sandbox testing and review.

See [production integration architecture](production-integration-architecture.md) and [finance demo scope](finance-automation-demo.md).

## Portfolio-safe summary

> Built a modular Python prototype for repeatable finance operations checks, using synthetic AR/AP, invoices, bank/ledger and timesheet records. Implemented deterministic exception detection, a review-only queue, Streamlit visualization, batch execution, local JSON report generation, and automated tests. Production financial connectors, secrets retrieval, AI inference, and general-purpose orchestration remain future integration work.
