# Finance scheduling: operational synthetic mode

This repository now includes a **working scheduled job entrypoint** for the synthetic finance engine. It runs reconciliation, AP/AR validation, invoice matching, timesheet exception checks and report generation. It **does not connect to live systems**, invoke LLM APIs, retrieve Bitwarden secrets or execute financial writes.

## One-time setup (macOS/Linux)

Use a trusted, always-on host with Python 3.10+ and a checked-out copy of this repository. Run from the repository root:

```bash
python3 -m finance.automation_runner --source synthetic --output-dir ./var/finance
```

Results are written with restricted permissions to `var/finance/latest.json` and `var/finance/runs.jsonl`. Keep these out of Git and restrict host access. The runner uses an exclusive process lock and atomic latest-result replacement.

## Scheduling is optional and use-case-specific

The repository has **no built-in recurring cron schedule**. The weekday 8 AM expression below is merely an example, not the default or a requirement for running this prototype. During local setup, the temporary weekday schedule was removed. Choose task frequency only after documenting the business process, data freshness, required approvals, and host availability. See the [local prototype guide](local-finance-prototype-guide.md).

## Cron configuration

Check the absolute repository path and Python interpreter (`command -v python3`). Edit your crontab using `crontab -e` and add, for example:

```cron
# Every weekday at 08:00 in the host's configured local timezone
0 8 * * 1-5 OPENCLAW_REPO=/absolute/path/to/marketing-openclaw-ai PYTHON_BIN=/absolute/path/to/python3 /bin/sh /absolute/path/to/marketing-openclaw-ai/scripts/run_finance_cron.sh >> /absolute/path/to/private/finance-cron.log 2>&1
```

Replace all example paths. The host must remain powered on; cron does not backfill missed runs. Use a private log path, configure log rotation, and monitor exit codes. Cron is appropriate for scheduled batches, not guaranteed real-time processing. On macOS, consider a launchd service for persistent scheduling.

## Readiness gates for live operation

1. Implement authorized source-specific API adapters and schema mapping; current runner explicitly rejects `--source live`.
2. Integrate Bitwarden secret retrieval through an authenticated, least-privilege runtime identity. Never put secret values in cron entries, shell history, environment files committed to Git, logs or Streamlit.
3. Configure provider-specific OAuth/token refresh, API limits, timeouts and retry policies.
4. Add opt-in LLM processing with redaction, schema validation and review-only outputs.
5. Add monitoring/alerting, data retention, backups and reconciliation against accounting ground truth.
6. Conduct sandbox and end-to-end tests with authorized accounts. Require human approvals for payments, accounting writes and payroll.

See [production architecture](production-integration-architecture.md) and [finance demo scope](finance-automation-demo.md).
