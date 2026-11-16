# Deploy the synthetic E-Commerce Operations Dashboard to Streamlit Community Cloud

This guide deploys a **public, synthetic-only** portfolio showcase. The deployed entrypoint forces demonstration mode and does not render file upload controls, access Shopify, submit Google Merchant API requests, or execute the agent's command-line tools.

## Repository already prepared

- Repository: `Tomas-Corza/marketing-openclaw-ai`
- Branch: `main`
- **Main file path:** `dashboard/public_app.py`
- Requirements: `dashboard/requirements.txt`
- Example product data: `examples/dashboard/`
- Local authorized-upload alternative: `dashboard/app.py` (do **not** use this as the public entrypoint).

## Publish from your Streamlit account

1. Sign in at https://share.streamlit.io with GitHub and authorize access to this repository.
2. Click **Create app**, then choose the option to deploy an existing GitHub app.
3. Select repository `Tomas-Corza/marketing-openclaw-ai`, branch `main` and file path **`dashboard/public_app.py`**.
4. Optionally choose an available subdomain, such as `marketing-openclaw-demo`. Streamlit decides if the name is available; do not assume it is yours.
5. Click **Deploy**. Verify the Overview and four remaining tabs, synthetic-only banner, and absence of file upload controls.
6. Copy the **actual deployed URL** shown by Streamlit before putting it on your portfolio. Do not guess the URL.

You must complete the Streamlit account authorization and deployment in its interface. This repository alone **does not** create a live hosted app.

## Local preview of public mode

```bash
python3 -m pip install -r dashboard/requirements.txt
streamlit run dashboard/public_app.py
```

To use authorized merchant uploads *locally* instead, run `streamlit run dashboard/app.py`; never use that general upload entrypoint as your public portfolio deployment.

## Portfolio CTA

Once Streamlit returns the live app URL, add this link to the AI Marketing Analytics page at https://tomascorza.me/ai-marketing-analytics:

```html
<a href="REPLACE_WITH_VERIFIED_STREAMLIT_URL" target="_blank" rel="noopener noreferrer">
  Explore the AI E-Commerce Operations Dashboard
</a>
```

Suggested description: "Explore a synthetic demonstration of Shopify catalog optimization, Merchant Center diagnostics, and approval-controlled feed changes using Marketing OpenClaw AI."

## Boundaries

- Public mode is intentionally **synthetic-only**. Approvals are temporary demonstrations and never publish to a store or Merchant Center.
- No API credentials should be configured in the public demo; the source repository is public.
- The public app contains no real account data; its fake product URLs are illustrative, not merchant landing pages.
- Upload support and integration credentials belong only in separately authenticated deployments.
- Deployment requires your Streamlit account approval. A successfully merged GitHub pull request does not prove deployment or uptime.

Official references:
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization
