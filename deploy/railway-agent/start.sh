#!/bin/sh
set -eu
: "${OPENCLAW_GATEWAY_TOKEN:?Set OPENCLAW_GATEWAY_TOKEN in Railway Variables}"
: "${OPENCLAW_PUBLIC_ORIGIN:?Set OPENCLAW_PUBLIC_ORIGIN to the new agent service HTTPS URL}"
case "$OPENCLAW_PUBLIC_ORIGIN" in
  https://*) ;;
  *) echo "OPENCLAW_PUBLIC_ORIGIN must start with https://" >&2; exit 1 ;;
esac
export OPENCLAW_GATEWAY_PORT="${PORT:-8080}"
export OPENCLAW_STATE_DIR="${OPENCLAW_STATE_DIR:-/data/.openclaw}"
export OPENCLAW_WORKSPACE_DIR="${OPENCLAW_WORKSPACE_DIR:-/data/workspace}"
mkdir -p "$OPENCLAW_STATE_DIR" "$OPENCLAW_WORKSPACE_DIR"
# Prepare Railway's /data mount for the unprivileged agent process.
chown -R node:node /data
exec gosu node /bin/sh -c '
  set -eu
  cd /opt/marketing-openclaw-ai
  python3 setup_skills.py --workspace "$OPENCLAW_WORKSPACE_DIR"
  for file in AGENTS.md IDENTITY.md SOUL.md HEARTBEAT.md; do
    if [ ! -e "$OPENCLAW_WORKSPACE_DIR/$file" ]; then
      cp "$file" "$OPENCLAW_WORKSPACE_DIR/$file"
    fi
  done
  if [ ! -f "$OPENCLAW_STATE_DIR/openclaw.json" ]; then
    python3 /opt/marketing-openclaw-ai/deploy/railway-agent/init_config.py
  fi
  exec openclaw gateway run --bind lan --port "$OPENCLAW_GATEWAY_PORT" --auth token
'
