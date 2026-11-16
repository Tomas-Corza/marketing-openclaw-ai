#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
[[ "$(uname -s)" == "Darwin" ]] || { echo "This installer targets macOS only" >&2; exit 2; }
command -v python3 >/dev/null || { echo "Python 3.10+ is required" >&2; exit 2; }
python3 -c 'import sys; assert sys.version_info >= (3,10), "Python 3.10+ required"'
skip=false
workspace="$HOME/.openclaw/workspace"
for arg in "$@"; do
  case "$arg" in
    --skip-openclaw) skip=true ;;
    --workspace=*) workspace="${arg#*=}" ;;
    -h|--help) echo "Usage: bash install.sh [--skip-openclaw] [--workspace=/absolute/path]"; exit 0 ;;
    *) echo "Unknown argument: $arg" >&2; exit 2 ;;
  esac
done
[[ "$workspace" == /* ]] || { echo "Workspace path must be absolute" >&2; exit 2; }
python3 setup_skills.py --workspace "$workspace" --dry-run
if [[ "$skip" == false ]] && ! command -v openclaw >/dev/null 2>&1; then
  echo "Official installer: https://openclaw.ai/install.sh"
  echo "It may install Node and launch interactive onboarding."
  read -r -p "Download and run the official OpenClaw installer? [y/N] " response
  [[ "$response" =~ ^[Yy]$ ]] || { echo "Declined. No OpenClaw installation attempted."; exit 1; }
  tmp="$(mktemp -t openclaw-install.XXXXXX)"
  trap 'rm -f "$tmp"' EXIT
  curl --fail --location --silent --show-error --proto '=https' --tlsv1.2 https://openclaw.ai/install.sh --output "$tmp"
  bash "$tmp"
fi
if [[ "$skip" == false ]] && ! command -v openclaw >/dev/null 2>&1; then
  echo "OpenClaw not in PATH; finish onboarding and reopen Terminal before rerunning." >&2
  exit 1
fi
python3 setup_skills.py --workspace "$workspace"
if [[ "$skip" == true ]]; then
  python3 verify_installation.py --workspace "$workspace" --skip-openclaw
else
  python3 verify_installation.py --workspace "$workspace"
fi
echo "Skill files deployed. Configure model, Gateway, and business integrations separately."
