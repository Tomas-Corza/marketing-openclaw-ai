# Shopify Product Page Automation (API-ready)

This is an API-ready, review-first Shopify content workflow aligned with Marketing OpenClaw AI. It has no live Shopify credentials or deployed scheduling. AI generation is handled by an external authorized agent/workflow; the Python utility audits, fetches, previews, and writes specifically approved content.

## Configuration

Use Python 3.10+ and Shopify GraphQL Admin API version `2026-10`. Create or authorize a Shopify app for the merchant's store with `read_products` and (to apply updates) `write_products`, plus the staff/app permissions necessary to update products. Obtain the Admin API access token through Shopify's supported app authentication process.

Keep the token out of the repository. Example local shell setup:

```bash
export SHOPIFY_SHOP_DOMAIN="your-store.myshopify.com"
export SHOPIFY_ACCESS_TOKEN="YOUR_AUTHORIZED_ACCESS_TOKEN"
```

Do not commit these variables, shell history with secrets, or exported merchant catalogs.

## Offline demonstration (no credentials)

```bash
python3 tools/shopify_product_pages.py audit --input examples/shopify_product_sample.json
```

## Authorized store commands

```bash
python3 tools/shopify_product_pages.py fetch --id 123456789
python3 tools/shopify_product_pages.py preview --id 123456789 --proposal examples/shopify_product_proposal.json
# ONLY after merchant approval for this exact change:
python3 tools/shopify_product_pages.py apply --id 123456789 --proposal examples/shopify_product_proposal.json --confirm
```

`preview` fetches the live current content but does **not** write it. `apply` makes a live Shopify API write. For production, add authorization logs, change backups, HTML sanitation, retries/backoff for throttling, and rollback procedures.

## Proposed content schema

```json
{
  "descriptionHtml": "<p>Verified, merchant-approved product description.</p>",
  "seo": {
    "title": "Example SEO title",
    "description": "Example SEO summary."
  }
}
```

Avoid asserting unsupported specifications, compliance, shipping promises, certifications or marketing results. Product page optimization is not proof of improved conversion.

Shopify reference: https://shopify.dev/docs/api/admin-graphql/2026-10/mutations/productUpdate
