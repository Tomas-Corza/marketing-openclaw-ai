# Shopify product feed creation automation

Convert an authorized Shopify product CSV export to Google Merchant Center-compatible TSV or RSS 2.0 XML. Runs offline with Python 3.10+ and no API credentials.

## Inputs and safety

Required CSV column headings: `Handle`, `Title`, `Body (HTML)`, `Variant SKU`, `Variant Price`. For usable output you should also provide `Vendor`, `Variant Barcode`, `Image Src`, `Variant Inventory Tracker`, `Variant Inventory Qty`, `Variant Inventory Policy`, and variant option values where applicable.

Only **actual sellable variant rows** (SKU or price populated) become items. Image-only rows are attached to their parent product. SKUs become feed IDs: they must be unique and stable across refreshes. Do not rely on this export to infer shipping eligibility or tax settings.

The converter checks required content, valid positive prices, stock-tracking data, links and basic identifiers. It rejects incomplete items and logs reasons separately. It does not auto-invent missing GTIN, manufacturer, shipping, stock, price or material information. **This is a starter feed, not a guarantee that every product meets Google Merchant Center policy.** Requirements vary by country and category (e.g. apparel, local inventory, multipacks, regulated goods).

## Generate a TSV feed

```bash
python3 tools/shopify_feed_builder.py \
  --input examples/shopify_merchant_feed_sample.csv \
  --store-url https://example.com \
  --currency USD \
  --output /tmp/merchant-feed.tsv \
  --rejects /tmp/merchant-feed-errors.json \
  --format tsv
```

For RSS XML, change `--format rss` and use a filename ending `.xml`.

- Store URL must be your real HTTPS storefront origin (not admin domain).
- USD and new are defaults: explicitly verify these match the actual prices and conditions.
- Tracked quantity > 0 becomes `in_stock`; 0 or less with deny policy becomes `out_of_stock`.
- Continue-selling items at 0 stock are rejected for merchant review instead of being treated as in stock automatically.
- For untracked products, the generator rejects them by default. Use `--untracked-in-stock` only when you can confirm they are actually in stock.
- Every output path must be new. This prevents silent overwriting. For automation, generate timestamped filenames and atomically switch your local feed-serving pointer only after validation.
- Feed prices and availability must match your storefront and target country. Product images must be reachable, and destination pages must work.

## Example scheduled local refresh (only after merchant authorization)

Export a fresh Shopify CSV **through an authorized process**, then run the generator on that file. A local cron job or task scheduler can run these commands at approved intervals. Example *generation only* (does not download Shopify data, schedule a job, host a feed, or upload to Merchant Center):

```bash
python3 tools/shopify_feed_builder.py --input /private/current-shopify-export.csv --store-url https://your-store.example --output /private/feeds/merchant-feed-$(date +%Y%m%d-%H%M%S).tsv --rejects /private/reports/rejected-$(date +%Y%m%d-%H%M%S).json
```

For production, implement verified Shopify GraphQL catalog pagination or Shopify Bulk Operations with a sanctioned API token; ensure exports contain variants, accurate inventory and images. Supply the resulting hosted HTTPS feed URL to Merchant Center, then monitor diagnostics. This repository does **not** yet fetch a catalog automatically, host a feed, or create Merchant Center schedules.

## Output columns

`id`, `title`, `description`, `link`, `image_link`, `availability`, `price`, `condition`, `brand`, `gtin`, `mpn`, `item_group_id`.

Check the Google Merchant Center product data specification before submitting, especially requirements for a particular target market, tax, shipping, GTIN, variant landing links, item groups, and availability.

## Tests

```bash
python3 -m unittest tests.test_shopify_feed_builder
```

Official reference: https://support.google.com/merchants/answer/7052112
