"""Scheduled, read-only finance validation runner. Standard library only.

Synthetic mode is the only built-in data source. Live input requires a separately
implemented, authorized adapter returning the finance.engine data schema.
"""
from __future__ import annotations
import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from finance.engine import seed_data, analyze, suggest_actions

def run(output_dir: Path, source: str = "synthetic") -> dict:
    if source != "synthetic":
        raise ValueError("Live source adapters are not implemented; refusing to run")
    output_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(output_dir, 0o700)
    lock_path = output_dir / ".finance.lock"
    with lock_path.open("a+") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("Another finance job is running") from exc
        data = seed_data()
        result = analyze(data)
        now = dt.datetime.now(dt.timezone.utc).isoformat()
        payload = {"timestamp_utc": now, "source": source, "read_only": True,
                   "summary": result["summary"], "exceptions": result["exceptions"],
                   "audit": result["audit"], "review_queue": suggest_actions(result)}
        serialized = json.dumps(payload, indent=2, sort_keys=True)
        digest = hashlib.sha256(serialized.encode()).hexdigest()
        fd, tmp = tempfile.mkstemp(prefix=".finance-", suffix=".json", dir=output_dir)
        try:
            with os.fdopen(fd, "w") as f:
                os.fchmod(f.fileno(), 0o600)
                f.write(serialized)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, output_dir / "latest.json")
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        with (output_dir / "runs.jsonl").open("a") as log:
            os.chmod(output_dir / "runs.jsonl", 0o600)
            log.write(json.dumps({"timestamp_utc": now, "sha256": digest,
                                  "source": source, "exception_count": len(result["exceptions"]),
                                  "status": "success"}) + "\n")
        return payload

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default=os.environ.get("OPENCLAW_FINANCE_OUTPUT_DIR", "var/finance"))
    parser.add_argument("--source", choices=["synthetic", "live"], default="synthetic")
    args = parser.parse_args()
    try:
        payload = run(Path(args.output_dir).expanduser().resolve(), args.source)
        print(json.dumps({"status": "success", "source": payload["source"],
                          "exceptions": len(payload["exceptions"])}))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "error", "message": str(exc)}), file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
