---
name: shopify-feed-sync
description: Fetch authorized Shopify product variants via GraphQL, generate validated Merchant Center-style feeds, and configure opt-in scheduled refresh and optional GitHub Pages hosting.
---

# Shopify Feed Sync

Use when building a Merchant Center-style feed directly from Shopify Admin GraphQL product and variant records without manually exporting CSV.

## Tools and setup
- `tools/shopify_live_feed_sync.py`
- `docs/shopify-live-feed-sync.md`
- GitHub Actions workflow: `.github/workflows/shopify-live-feed.yml`
- Reuses `tools/shopify_feed_builder.py`.
- Shopify credentials: private `SHOPIFY_SHOP_DOMAIN` and `SHOPIFY_ACCESS_TOKEN` with authorized catalog read access.

## Workflow
1. Confirm merchant approval to access the store and, separately, any permission to publish product details publicly.
2. From the repository root, run an authorized local feed build:
   `python3 tools/shopify_live_feed_sync.py --store-url https://your-store.example --currency USD --format rss --output /private/feed.xml --rejects /private/rejected.json`.
3. Review rejected variants and Merchant Center feed requirements; strict mode refuses partial feeds. Do not bypass incomplete product data merely to publish.
4. To enable daily GitHub Actions generation, configure Shopify credentials in repository **Secrets**, storefront URL and currency as **Variables**, then set `ENABLE_SHOPIFY_FEED_SYNC=true` only when approved.
5. Public GitHub Pages hosting requires a **separate** authorization and `ENABLE_PUBLIC_FEED_PAGES=true` plus repository Pages configuration.
6. Verify scheduled workflow runs, actual hosted feed URL, Merchant Center diagnostics, matching variant landing pages, shipping, stock and pricing accuracy.

## Guardrails
- This reads Shopify; it does not change Shopify products or send updates to Merchant Center.
- The workflow is **disabled by default** and GitHub schedules are best-effort.
- Feed output may require additional country- or category-specific attributes; source availability may not represent every location/channel.
- Do not publish private or restricted merchandise catalog information without authorization.
- Production setup and live end-to-end validation are required before claiming successful automated feed delivery.

Related skills: `shopify-product-feed-builder`, `merchant-feed-diagnostics`.
