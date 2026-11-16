---
name: shopify-product-feed-builder
description: Convert authorized Shopify product CSV exports to validated Google Merchant Center-style TSV or RSS XML feeds and inspect rejected items.
---

# Shopify Product Feed Builder

Use when creating a product feed from a Shopify CSV export **without** a live Shopify API connection. For direct API-based catalog refresh and scheduling, use `shopify-feed-sync`.

## Tools
- `tools/shopify_feed_builder.py`
- `docs/shopify-product-feed-builder.md`
- Sample: `examples/shopify_merchant_feed_sample.csv`

## Workflow
1. Obtain a merchant-authorized Shopify export containing reliable variant SKUs, prices, inventory, product descriptions, images and product identifiers.
2. Run from the repository root:
   `python3 tools/shopify_feed_builder.py --input examples/shopify_merchant_feed_sample.csv --store-url https://example.com --output /tmp/merchant-feed.tsv --rejects /tmp/merchant-errors.json --format tsv`.
3. For an RSS XML output, use `--format rss` and an `.xml` output path.
4. Read the JSON reject report; verify SKU uniqueness, product/variant URLs, identifiers, stock availability, accurate prices and source descriptions.
5. Review Merchant Center requirements for the targeted country, product category, shipping, tax and other relevant attributes before separately submitting any feed.

## Guardrails
- Local file generation only. This script does not pull Shopify data, host a feed, upload to Merchant Center or schedule refreshes.
- Untracked inventory is rejected unless the merchant explicitly verifies availability and opts in. Never infer that oversold variants are immediately available.
- Product SKU is used as item ID in this export mode; do not assume handles are unique variant IDs.
- Verify that each submitted variant has a matching landing page and that feed prices and availability match the site.
- Do not expose private catalog data or assume passing offline checks guarantees Merchant Center approval.

Related skills: `shopify-feed-sync`, `merchant-feed-diagnostics`.
