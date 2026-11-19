#!/bin/sh
# Run from cron on a trusted host; configure OPENCLAW_REPO and PYTHON_BIN.
set -eu
umask 077
REPO="${OPENCLAW_REPO:?Set OPENCLAW_REPO to an absolute repository path}"
case "$REPO" in /*) ;; *) echo "OPENCLAW_REPO must be absolute" >&2; exit 2;; esac
PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python3}"
cd "$REPO"
exec "$PYTHON_BIN" -m finance.automation_runner --source synthetic --output-dir "${OPENCLAW_FINANCE_OUTPUT_DIR:-$REPO/var/finance}"
