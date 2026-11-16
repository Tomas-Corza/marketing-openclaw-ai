# Live Shopify catalog feed sync (opt-in)

This extension reads authorized Shopify product variants through the **Shopify GraphQL Admin API** and generates a Google Merchant Center-style RSS XML feed. A GitHub Actions schedule can regenerate it daily and, if explicitly enabled, deploy the feed using GitHub Pages.

## 1. Authorize credentials

Create or install an authorized Shopify app with permission to read product details, variant prices, identifiers, images and inventory. At minimum, review the `read_products` permission; additional access may be required for particular inventory/data configurations. Grant only permissions needed for the store.

In **GitHub → repository Settings → Secrets and variables → Actions**, configure:

| Type | Name | Value |
| --- | --- | --- |
| Secret | `SHOPIFY_SHOP_DOMAIN` | `your-store.myshopify.com` |
| Secret | `SHOPIFY_ACCESS_TOKEN` | authorized Shopify Admin API token |
| Variable | `SHOPIFY_STOREFRONT_URL` | `https://your-store.com` |
| Variable | `SHOPIFY_FEED_CURRENCY` | `USD` or actual feed currency |
| Variable | `ENABLE_SHOPIFY_FEED_SYNC` | `true` **only when authorized** |

Never commit API tokens or actual merchant exports. For stores with sensitive, restricted or ineligible merchandise, obtain merchant and policy approval before running or publishing.

## 2. Generate now (local)

```bash
export SHOPIFY_SHOP_DOMAIN="your-store.myshopify.com"
export SHOPIFY_ACCESS_TOKEN="your-token-from-secure-storage"

python3 tools/shopify_live_feed_sync.py \
  --store-url https://your-store.com \
  --currency USD \
  --format rss \
  --output /private/merchant-feed.xml \
  --rejects /private/rejected-items.json
```

The script:
- Paginates Shopify ProductVariants in batches of 100.
- Skips inactive products or those without an online store URL.
- Creates stable feed IDs from numeric Shopify variant IDs (not editable SKUs).
- Reads current price, inventory tracking, inventory quantity, product descriptions, barcodes and images.
- Reuses the product-feed builder's validations and outputs valid RSS/TSV with a reject report.
- Refuses to generate a feed in strict mode if any items are rejected, to avoid silently publishing a reduced catalog.

For intentionally partial feeds, `--allow-partial` generates valid entries while logging rejected variants. The workflow defaults to **strict mode**.

## 3. Schedule daily refresh in GitHub Actions

Workflow: `.github/workflows/shopify-live-feed.yml`.

The workflow runs daily at **10:17 UTC** (GitHub schedules are best-effort and may be delayed) and supports manual dispatch. It performs **nothing unless** the repository variable `ENABLE_SHOPIFY_FEED_SYNC=true`.

Once enabled, it creates a validated feed and a seven-day GitHub Actions artifact. This does not alter product content in Shopify.

### Optional public feed hosting

To publish the validated RSS feed publicly:

1. Confirm the catalog is suitable for public publication.
2. In repository **Settings → Pages**, select **GitHub Actions** as the build and deployment source.
3. Set GitHub Actions variable `ENABLE_PUBLIC_FEED_PAGES=true` (leave unset or false otherwise).
4. Run the workflow and verify the deployment. An example Pages location is `https://USERNAME.github.io/REPO/merchant-feed.xml`; use the actual deployed Pages URL, do not assume it.
5. Configure Merchant Center to fetch this public URL on the desired cadence and monitor Merchant Center diagnostics and policy requirements.

Only `public/merchant-feed.xml` is uploaded to Pages. The reject report is stored in the private workflow artifact (access still depends on repository permissions). Feed publication is disabled by default. Never publish customer information.

## Operational limitations

- This is an authorized read-only Shopify integration: it does not write products or call Google Merchant Center APIs.
- Product URL currently points to the product page, not a variant-specific `?variant=...` URL. Check that the page clearly matches each submitted variant's price and selections; production deployments should implement variant-deep links.
- Variant price, inventory and images need review for market, channel, location, country, tax and currency rules.
- Inventory is not location-scoped. Untracked inventory is rejected by default; strict mode rejects unknown availability and oversold items.
- It does not add shipping, tax, Google product category, apparel attributes or regulatory metadata automatically. Check the official Merchant Center product data specification for your market/category.
- Scheduled GitHub workflow runs may be delayed or disabled by GitHub conditions. Monitor successful workflows, reject reports and Merchant Center diagnostics.
- API response/rate-limit errors abort the build; a failed Pages build should not overwrite a previous successfully published feed.
- No live Shopify store or Merchant Center validation has been performed as part of the repository implementation.

## Tests

```bash
python3 -m unittest tests.test_shopify_live_feed_sync tests.test_shopify_feed_builder
```

References:
- https://shopify.dev/docs/api/admin-graphql/2026-10/queries/productVariants
- https://support.google.com/merchants/answer/7052112
- https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#schedule
