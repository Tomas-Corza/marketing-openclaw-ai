#!/usr/bin/env python3
"""Read-only deployment checks; not an end-to-end business integration test."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from setup_skills import names

def verify(workspace, check_openclaw=True):
    root = Path(workspace)
    found = names()
    checks = {"skill:" + name: (root / "skills" / name / "SKILL.md").is_file() for name in found}
    for rel in ("tools/customer_inquiry_assistant.py", "tools/shopify_return_processing.py",
                "tools/shopify_product_pages.py", "tools/gmail_inquiry_drafts.py"):
        checks[rel] = (root / rel).is_file()
    if check_openclaw:
        executable = shutil.which("openclaw")
        checks["openclaw_cli"] = bool(executable)
        if executable:
            try:
                checks["openclaw_version"] = subprocess.run(
                    [executable, "--version"], timeout=15, capture_output=True).returncode == 0
            except (OSError, subprocess.TimeoutExpired):
                checks["openclaw_version"] = False
    return {"passed": all(checks.values()), "skill_count": len(found),
            "checks": checks, "note": "No live provider, skill execution, or external account testing performed."}

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workspace", type=Path, default=Path.home() / ".openclaw/workspace")
    p.add_argument("--skip-openclaw", action="store_true")
    a = p.parse_args()
    result = verify(a.workspace, check_openclaw=not a.skip_openclaw)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["passed"] else 1)
