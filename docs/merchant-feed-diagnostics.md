# Product Feed Diagnostics Agent

Audit Google Merchant Center-style **TSV or RSS XML** feeds offline, optionally combine the results with real Google Merchant API product issues, and generate prioritized remediation advice. **All fixes are local, snapshot-checked and approval-gated.** This skill never changes Shopify products, Google Merchant Center account settings, or live feed hosting.

## 1. Audit a feed offline

```bash
python3 tools/merchant_feed_diagnostics.py audit \
  --feed /private/merchant-feed.tsv \
  --output /private/merchant-diagnostics.json
```

To audit XML, pass `--feed /private/merchant-feed.xml`.

Flags missing descriptions, titles, duplicate IDs, invalid HTTPS URLs, unsupported availability values, malformed/zero prices, GTIN checksum errors, and basic identifier gaps. Some checks are intentionally conservative and are **not** complete Google Merchant Center policy validation.

## 2. Use an authorized Merchant API snapshot (optional)

Google Merchant API v1 endpoint: `GET /products/v1/accounts/{ACCOUNT_ID}/products`. It returns processed products and asynchronous `productStatus.itemLevelIssues` plus destination approval statuses.

Acquire a **short-lived OAuth2 access token** authorized for this Merchant Center account with the `https://www.googleapis.com/auth/content` scope. Use a secret manager or private environment; do not commit credentials. OAuth token creation/refresh and account onboarding are not implemented by this connector.

```bash
export MERCHANT_API_ACCESS_TOKEN="YOUR_SHORT_LIVED_OAUTH_TOKEN"
python3 tools/merchant_api_connector.py \
  --account-id 123456789 \
  --output /private/merchant-status.json

python3 tools/merchant_feed_diagnostics.py audit \
  --feed /private/merchant-feed.tsv \
  --merchant-json /private/merchant-status.json \
  --output /private/combined-diagnostics.json
```

A synthetic API snapshot is available in `examples/merchant_api_status_sample.json` for offline demonstrations.

The connector paginates `accounts.products.list` and makes **GET requests only**. Real account results depend on access rights, API quotas, and Merchant Center processing time. API data and feed item IDs may not map one-to-one: investigate aliases or differing feed labels before remediation. Warnings and disapprovals are different types of findings.

## 3. Optional AI issue triage

With merchant permission to send diagnostics to an AI provider, export a report and run:

```bash
export OPENAI_API_KEY="YOUR_PRIVATE_API_KEY"
python3 tools/merchant_feed_ai_triage.py \
  --report /private/combined-diagnostics.json \
  --output /private/merchant-ai-remediation.json \
  --max-issues 30
```

The OpenAI Responses API returns structured issue-level remediation suggestions and verification tasks, not a feed-editing manifest. Product issue descriptions are untrusted data. The generated suggestions can still be inaccurate or incomplete and need expert review. This costs API tokens; a ChatGPT subscription does not supply API credits. Data sent includes offer ID, issue code, priority, message and field, so obtain permission for that data transfer.

## 4. Approval-controlled local fixes

Prepare a **private** JSON file containing proposed changes keyed by existing feed ID (do not invent identifiers):

```json
{
  "sku-123": {"title": "Merchant-verified product title"}
}
```

Build a review manifest (all entries start with approved=false):

```bash
python3 tools/merchant_feed_diagnostics.py draft \
  --feed /private/merchant-feed.tsv \
  --changes /private/reviewed-changes.json \
  --output /private/approval-manifest.json
```

Check each proposed correction against the authoritative storefront and item facts. Only then set `approved: true` for specific entries. Rejected entries should be removed. Apply the **local output only**:

```bash
python3 tools/merchant_feed_diagnostics.py apply \
  --feed /private/merchant-feed.tsv \
  --manifest /private/approval-manifest.json \
  --output /private/approved-feed.tsv \
  --confirm
```

The apply command validates unique IDs, allowed text attributes, approved flags, and SHA-256 feed item snapshots to prevent editing data changed since approval. Price, availability, ID, item grouping and inventory changes are excluded from automatic patching. Outputs never overwrite existing files. Re-audit the resulting file and inspect it manually before replacing any live published feed. The XML writer creates a standalone **review-only** RSS document with an example channel URL; a production deployment must preserve a correct channel URL.

## Scope and restrictions

- No automatic Google Merchant API writes or Shopify product edits.
- No automatically generated fix manifests from AI recommendations.
- No autonomous schedule or public publishing in this skill. The existing Shopify feed pipeline handles separately approved schedules.
- Feed compliance depends on target country, category, shipping/tax settings, manufacturer data, policies, and landing page accuracy. Treat uncertain commercial or regulatory data as a review task.
- Keep diagnostics, OAuth tokens and review manifests out of public repositories.

## Offline tests

```bash
python3 -m unittest tests.test_merchant_feed_diagnostics tests.test_merchant_feed_ai_triage
```

Official docs:
- https://developers.google.com/merchant/api/reference/rest/products_v1/accounts.products/list
- https://developers.google.com/merchant/api/reference/rest/products_v1/accounts.products
