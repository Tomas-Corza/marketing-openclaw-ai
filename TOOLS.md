# TOOLS.md — Integration notes (example)

This is a public template, not a record of installed or working integrations.

## Optional integration categories

- E-commerce analytics (for example, Shopify API)
- Email marketing analytics (for example, Klaviyo API)
- Reporting exports (for example, Google Sheets API)
- Public competitor and search research\n- Social-platform content analytics (authorized APIs or exports; not connected by default)

For each integration, document prerequisites, permissions, environment-variable names, rate limits, error handling, and data-retention policies. Put credentials only in locally managed secret storage. Never commit `.env`, service-account JSON keys, OAuth tokens, or real customer exports.

No integrations are enabled by this file alone.

## Marketing Analysis Tools

### Jobs-to-be-Done Analysis
- Skill: `skills/jtbd-analysis/SKILL.md`
- Script: `jtbd/analyze.py`
- Purpose: Compare marketing messages using Jobs-to-be-Done motivations.
- Input: CSV containing variant, job, delivered, clicks.

### Email Marketing Analytics
- Skill: `skills/email-analytics/SKILL.md`
- Script: `tools/email_analytics.py`
- Purpose: Analyze email campaign engagement and revenue.
- Input: CSV containing campaign, sent, clicks, orders, revenue.

### Social Media Behavior Monitor
- Skill: `skills/social-behavior-monitor/SKILL.md`
- Script: `tools/social_behavior_monitor.py`
- Connector contract: `tools/social_behavior_connector.py`
- Schema and setup: `docs/social-behavior-monitor.md`
- Example: `examples/social_behavior_sample.csv`
- Purpose: Summarize authorized social media engagement at the content level.
- Input: Normalized CSV; platform-specific APIs require separately implemented and approved adapters.

## Execution Guidelines

- Run scripts from the project root directory.
- Only process authorized datasets.
- Use synthetic data for demonstrations.
- Never invent marketing performance results.
- Explain findings in clear, nontechnical language.
- Do not modify live campaigns without approval.

### Shopify Bulk Feed Optimization
- Skill: `skills/shopify-product-page-automation/SKILL.md`
- Script: `tools/shopify_bulk_feed.py`
- Setup: `docs/shopify-bulk-feed-optimization.md`
- Example: `examples/shopify_bulk_feed_sample.csv`
- Purpose: Offline Shopify product CSV audits and explicit-approval API updates with product ID verification, per-product snapshot checks, and private audit logs.
- Access: No credentials for CSV audit; authenticated Shopify Admin GraphQL API required for prepare/apply.
- Publishing: Never run `apply --confirm` without explicit authorization for the exact proposed changes.

### AI Shopify Product Copy Generator
- Skill: `skills/shopify-product-page-automation/SKILL.md`
- Script: `tools/shopify_ai_copy.py`
- Guide: `docs/shopify-ai-copy-generation.md`
- Input: Authorized Shopify CSV product export; source title, vendor, type and existing description only.
- Output: Review-only AI title, HTML description, SEO metadata, JTBD messaging hypothesis and review notes.
- Credentials: Locally managed `OPENAI_API_KEY` and optional `OPENAI_MODEL`; requests go to the OpenAI Responses API.
- No automatic Shopify publishing; require independently verified product IDs and merchant approval.

### Shopify Product Feed Builder
- Script: `tools/shopify_feed_builder.py`
- Guide: `docs/shopify-product-feed-builder.md`
- Input: authorized Shopify product CSV export with variant SKU, price, inventory and product assets.
- Output: TSV or RSS XML Merchant Center-style feed and JSON rejected-item report.
- Access: offline; no Shopify credentials, Merchant Center publishing or scheduled sync included.
- Guardrails: validate source facts, prices, shipping, landing pages and Merchant Center policy before submission.

### Scheduled Shopify Merchant Feed Sync
- Script: `tools/shopify_live_feed_sync.py`
- Skill: `skills/shopify-product-page-automation/SKILL.md`
- Setup: `docs/shopify-live-feed-sync.md`
- Workflow: `.github/workflows/shopify-live-feed.yml`
- Access: authorized Shopify GraphQL Admin API credentials in secrets; product catalog read-only.
- Guardrails: schedule disabled until `ENABLE_SHOPIFY_FEED_SYNC=true`; public Pages deployment independently disabled until `ENABLE_PUBLIC_FEED_PAGES=true`.
- Validation: reject invalid products, verify Merchant Center requirements and price/availability landing-page alignment before publishing.
