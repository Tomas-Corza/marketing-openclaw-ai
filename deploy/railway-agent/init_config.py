"""Create minimal first-boot Gateway configuration; never store provider secrets."""
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

origin = os.environ["OPENCLAW_PUBLIC_ORIGIN"].rstrip("/")
url = urlsplit(origin)
if url.scheme != "https" or not url.hostname or url.username or url.password or url.path or url.query or url.fragment:
    raise SystemExit("OPENCLAW_PUBLIC_ORIGIN must be the HTTPS origin only, e.g. https://agent.example.com")
state = Path(os.environ["OPENCLAW_STATE_DIR"])
path = state / "openclaw.json"
config = {
    "gateway": {
        "mode": "local",
        "bind": "lan",
        "port": int(os.environ["OPENCLAW_GATEWAY_PORT"]),
        "auth": {"mode": "token"},
        "controlUi": {"allowedOrigins": [origin]},
    },
    "agents": {"defaults": {"workspace": os.environ["OPENCLAW_WORKSPACE_DIR"]}},
}
state.mkdir(parents=True, exist_ok=True)
with path.open("x", encoding="utf-8") as stream:
    json.dump(config, stream, indent=2)
path.chmod(0o600)
print("Created first-boot OpenClaw config (credentials excluded).")
