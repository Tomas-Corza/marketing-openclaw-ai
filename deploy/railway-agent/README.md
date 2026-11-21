# Deploy Marketing OpenClaw AI agent to Railway

This is a **separate agent service**. Do not alter the working Streamlit dashboard service or configure Railway to use this Dockerfile globally.

## Create a new service from this repository

1. In Railway, create a **new service** using `Tomas-Corza/marketing-openclaw-ai` and select branch `railway-agent-deployment` for testing. Root directory: `/`.
2. In service Settings, set the Dockerfile path to `deploy/railway-agent/Dockerfile`. Do not set a Streamlit start command.
3. Attach one persistent Railway volume mounted at `/data`. Run **one replica**: this state directory is not built for simultaneous writers.
4. Generate a **new service domain** in Networking; set target port to **8080**.
5. Set variables on **this agent service only**:
   - `PORT=8080`
   - `OPENCLAW_GATEWAY_TOKEN`: long, random unique secret, generated outside GitHub.
   - `OPENCLAW_PUBLIC_ORIGIN=https://<new-agent-domain>.up.railway.app` (no trailing slash or path)
   - Optional provider credentials, after reviewing provider docs (e.g. `OPENAI_API_KEY`). Never paste keys into GitHub or logs.
6. Deploy and verify logs, then authenticate in the Control UI with the Gateway token. A model provider still needs authorized configuration before the agent can respond.

This container installs OpenClaw, copies the existing OpenClaw skill files into the persistent workspace **without overwriting changed files**, and runs its authenticated Gateway. Existing state/configuration persists on the Railway volume. It does not configure Shopify, Gmail, finance or other live APIs. It does not enable recurring workflows or external writes.

**Security:** Treat the Gateway token as an admin secret. Protect the public domain; use stronger private network access where possible. Do not expose customer data or business credentials until reviewed. The first-boot configuration explicitly allows only the stated browser origin. If you change the agent domain after first startup, update `gateway.controlUi.allowedOrigins` in the persistent configuration; environment changes alone do not rewrite it. Public access to an authenticated agent still carries meaningful risk.

**Validation:** This deployment configuration has not yet been tested on Railway. Review build/start logs, authenticate, and run `openclaw doctor` and a synthetic test before representing it as a working cloud agent.

**References:** https://docs.openclaw.ai/install/railway · https://docs.openclaw.ai/gateway/security/network-exposure
