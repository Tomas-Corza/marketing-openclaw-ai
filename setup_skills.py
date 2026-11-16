#!/usr/bin/env python3
"""Install OpenClaw skills and shared tools without overwriting existing files."""
import argparse
import filecmp
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent
SUBDIRS = ("skills", "tools", "docs", "examples")

def names(root=ROOT):
    output = []
    for folder in sorted((root / "skills").iterdir()):
        if folder.is_symlink():
            raise ValueError("Symlink skill directory")
        if folder.is_dir():
            marker = folder / "SKILL.md"
            if marker.is_symlink() or not marker.is_file():
                raise ValueError("Missing SKILL.md: " + folder.name)
            text = marker.read_text(encoding="utf-8")
            if not text.startswith("---\n") or "\nname:" not in text or "\ndescription:" not in text:
                raise ValueError("Invalid skill metadata: " + folder.name)
            output.append(folder.name)
    if not output:
        raise ValueError("No skills found")
    return output

def plan(workspace, root=ROOT):
    if workspace.is_symlink():
        raise ValueError("Workspace symlinks are not allowed")
    pending, existing, conflicts = [], [], []
    for dirname in SUBDIRS:
        source_dir = root / dirname
        if not source_dir.is_dir() or source_dir.is_symlink():
            raise ValueError("Unsafe or missing source: " + dirname)
        for source in sorted(source_dir.rglob("*")):
            if source.is_symlink():
                raise ValueError("Source symlink is not allowed: " + str(source))
            if not source.is_file() or "__pycache__" in source.parts or source.suffix in (".pyc", ".pyo"):
                continue
            relative = source.relative_to(root)
            if source.stat().st_size > 4_000_000:
                raise ValueError("Unexpectedly large deployment file: " + str(relative))
            target = workspace / relative
            parents = list(target.parents)
            if any(p.is_symlink() for p in [target] + parents[:parents.index(workspace)+1] if workspace in parents):
                conflicts.append(relative)
            elif target.exists():
                if target.is_file() and filecmp.cmp(source, target, shallow=False):
                    existing.append(relative)
                else:
                    conflicts.append(relative)
            else:
                pending.append((source, relative))
    return pending, existing, conflicts

def install(workspace, dry_run=False, root=ROOT):
    skills = names(root)
    workspace = Path(workspace).expanduser()
    pending, existing, conflicts = plan(workspace, root)
    if conflicts:
        raise ValueError("Conflicts detected; no files changed: " + ", ".join(map(str, conflicts[:20])))
    if not dry_run:
        workspace.mkdir(parents=True, exist_ok=True)
        for source, relative in pending:
            target = workspace / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            with source.open("rb") as reader, target.open("xb") as writer:
                shutil.copyfileobj(reader, writer)
            target.chmod(0o644)
    return {"workspace": str(workspace), "skills": skills, "new_files": len(pending),
            "already_identical": len(existing), "dry_run": dry_run}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.home() / ".openclaw/workspace")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(install(args.workspace, args.dry_run), indent=2))
    except (OSError, ValueError) as exc:
        print("Install failed: " + str(exc), file=sys.stderr)
        sys.exit(1)
