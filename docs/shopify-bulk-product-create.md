# Bulk Shopify Draft Product Creation from CSV

Import reviewed product catalogs with SKUs, prices and variants into Shopify as **unpublished DRAFT products**. The tool is part of the existing shopify-product-page-automation skill.

## CSV format

Use the fictional example at examples/shopify_bulk_product_create_sample.csv. Each row is one variant. Required exact column headers:

    handle,title,description_html,vendor,product_type,seo_title,seo_description,tags,option1_name,option1_value,option2_name,option2_value,option3_name,option3_value,sku,price

- Rows with the same handle form one product. Product-level fields must agree across its rows.
- Each variant needs a unique SKU within the file and a price in the store's currency.
- Up to three named options per product (e.g., Finish, Size). A single-variant product should use Style / Standard.
- Tags use a vertical bar delimiter (e.g. home|lighting).
- Input capped at 2 MB, 1,000 rows, 100 previewed products and 100 variants per product.
- Live import capped at 25 products per run, default 10.

## Review without credentials

From the repository root:

    python3 -m tools.shopify_bulk_product_create preview --input examples/shopify_bulk_product_create_sample.csv

The preview prints all proposed products, SKUs, prices, options, fixed DRAFT status, and an SHA-256 fingerprint for the exact CSV bytes.

## Create approved drafts

Configure private environment variables SHOPIFY_SHOP_DOMAIN and SHOPIFY_ACCESS_TOKEN for a merchant-authorized app with write_products permissions.

    python3 -m tools.shopify_bulk_product_create preview --input /private/catalog.csv

After a responsible merchant representative approves the exact content, target shop, prices and variant options:

    python3 -m tools.shopify_bulk_product_create create --input /private/catalog.csv --approve-sha256 EXACT_PREVIEW_SHA --confirm --journal /private/new-import-log.jsonl --max-products 10

The importer checks whether Shopify already contains each product handle. It stops on a matching handle instead of updating the product. A private, owner-readable log records attempted and completed creations. Do not reuse a journal filename; the importer refuses to overwrite it.

**Partial failures:** A Shopify timeout can occur after a product was created. This tool stops on the first failure. Check the import log and Shopify Admin before running any further imports. Never automatically retry the whole file.

## Boundaries

- Creates only DRAFT products and options/variants with prices and SKUs. Does **not** publish, add product images, set inventory, apply tax rules, generate AI copy, or create an entire Shopify storefront.
- Importing does not verify existing SKUs against a merchant's complete product catalog or guarantee duplicate prevention during concurrent jobs.
- Pricing values are provided by the merchant; no currencies are converted. The shop's currency applies.
- Live products, staff permissions and Shopify API behavior require an authorized development-store test before production use.
- Never commit merchant data, API credentials, or private logs.
- Technical approval flags and SHA-256 checks do not substitute for the merchant's permission.

## Offline tests

    python3 -m unittest discover -s tests -p 'test_shopify_bulk_product_create.py' -v

Shopify references:
- https://shopify.dev/docs/api/admin-graphql/2026-10/mutations/productSet
- https://shopify.dev/docs/api/admin-graphql/2026-10/input-objects/ProductSetInput
- https://shopify.dev/docs/api/admin-graphql/2026-10/input-objects/ProductVariantSetInput
