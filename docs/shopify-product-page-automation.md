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

## Create a new Shopify product draft (approval required)

The new `tools/shopify_product_create.py` utility creates **one new Shopify DRAFT** from merchant-verified JSON. Use `examples/shopify_new_product_sample.json` as a fictional schema reference and copy it outside the repository for real catalog data.

```bash
python3 -m tools.shopify_product_create preview --input /private/new-product.json
# Review the displayed product fields, images and input_sha256; obtain merchant approval.
python3 -m tools.shopify_product_create create --input /private/new-product.json --approve-sha256 THE_EXACT_PREVIEW_SHA --confirm
```

The script validates the supplied title, description HTML, vendor, product type, handle, SEO fields, tags and up to ten HTTPS image URLs. It sends Shopify GraphQL `productCreate` with an explicit `status: DRAFT`, displays the resulting Shopify product ID and does **not** publish the product. Shopify requires the `write_products` scope and product-creation permission. Image processing may still be pending after creation.

**Limits:** One product per command. No auto-generated AI copy, catalog CSV import, SKU, variants, price, inventory, duplicate detection or online-store publishing. Review and configure those separately. Re-running after an uncertain network failure can create duplicates; inspect the Shopify admin before retrying. The hash detects changed input, but does not itself verify merchant identity or permission. An authorized development-store end-to-end test is still required before production use.

Shopify docs: https://shopify.dev/docs/api/admin-graphql/2026-10/mutations/productCreate
