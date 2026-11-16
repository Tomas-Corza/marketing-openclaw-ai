# Shopify Bulk Feed Optimization

This extension adds an offline Shopify CSV product-feed audit and a strictly permissioned, product-ID-based batch update path. It **does not** generate AI copy by itself, import Google Merchant Center feeds, change price/inventory, or automatically publish audit results. Python 3.10+ and the standard library are sufficient.

## 1. Audit a Shopify CSV export (offline)

Obtain an authorized Shopify product CSV export with the columns `Handle`, `Title`, and `Body (HTML)`. Optional columns include `Vendor`, `Type`, `SEO Title`, and `SEO Description`.

```bash
python3 tools/shopify_bulk_feed.py analyze \
  --input examples/shopify_bulk_feed_sample.csv \
  --output /tmp/shopify-bulk-audit.json
```

- Consolidates variant/image rows by product handle.
- Flags missing short descriptions and SEO content using deterministic checks.
- Builds draft SEO title and meta description suggestions only from existing product text.
- Exports JSON with product-level findings and recommendations.
- Does **not** connect to Shopify or publish changes.

Do not assume these suggestions are SEO wins or fully compliant merchant claims. Always review them for relevance, length, accuracy, accessibility and brand requirements.

## 2. Prepare an authorized API review manifest

CSV handles are **not** reliable Shopify Product IDs. For authorized live updates, assemble the numeric IDs or Product GIDs from verified Shopify Admin records in a private local JSON file, for example:

```json
["123456789", "987654321"]
```

Ensure your shell has `SHOPIFY_SHOP_DOMAIN` and `SHOPIFY_ACCESS_TOKEN` configured using the Shopify app authorization process, with `read_products` permission (and `write_products` to later publish). See `docs/shopify-product-page-automation.md`.

```bash
python3 tools/shopify_bulk_feed.py prepare \
  --input /private/product_ids.json \
  --output /private/shopify-review-manifest.json
```

This fetches current Shopify product content and writes a manifest with `expected_sha256` snapshots, conservative `changes` proposals and `approved: false`. It does **not** publish.

## 3. Review and approve the exact product changes

Check every product ID and approved change. Manually edit `changes` to approved title, `descriptionHtml`, and/or `seo` fields, then set `approved` to `true` **only** for entries explicitly approved by an authorized merchant.

Example manifest entry (illustrative snapshot hash only; use the actual prepare-generated hash):

```json
{
  "id": "gid://shopify/Product/123456789",
  "expected_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
  "changes": { "seo": { "title": "Approved SEO title" } },
  "approved": true
}
```

Remove any unapproved entries before applying. Never bypass the snapshot check. The hash protects against product title, HTML description, or SEO text changes between preparation and publication (not against other product-field changes).

## 4. Apply in a capped batch after approval

```bash
python3 tools/shopify_bulk_feed.py apply \
  --input /private/shopify-review-manifest.json \
  --output /private/shopify-update-log.jsonl \
  --confirm --limit 25 --delay 0.75
```

The script checks every product's current snapshot before making its write. It stops on any stale snapshot, missing product, or Shopify update error. The append-only JSONL log includes pre-update content to support manual rollback. The run is **not atomic**: some products may be updated before an error. It has no automatic rollback, exponential retry or Shopify bulk mutation orchestration. Limit each run to at most 100 products; for larger catalogs, schedule separately reviewed chunks with audit logs and API throttling controls. Use a **new** output path for every run.

Do not commit merchant feeds, identifiers, snapshots, access tokens, or logs to a public repository. The sample contains synthetic products only.

## AI integration

The OpenClaw agent can consume the audit JSON and independently propose rewritten content using verified merchant product details and Jobs-to-be-Done messaging. The operator must then explicitly review proposed changes and link them to verified Shopify Product IDs via the approval manifest. **AI content generation and automated CSV-handle-to-ID matching are not implemented**. This separation prevents publishing fabricated attributes or writing to the wrong product.

## Testing

```bash
python3 -m unittest tests.test_shopify_bulk_feed
```
