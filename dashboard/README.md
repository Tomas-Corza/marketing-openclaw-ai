# AI E-Commerce Operations Dashboard

A Streamlit control center for the Marketing OpenClaw AI repository, designed for **offline demonstrations and controlled human review**. Upload merchant-authorized inputs or use the bundled synthetic fixtures. The dashboard does not create live Shopify, Google Merchant, or OpenAI API connections.

## Launch

From the repository root with Python 3.10+:

```bash
python -m pip install -r dashboard/requirements.txt
streamlit run dashboard/app.py
```

The synthetic demonstration dataset loads automatically. No API credentials are needed.

## Five dashboard views

| View | Integrations |
| --- | --- |
| Overview | Catalog/feed KPI cards, counts of issues and pending work |
| Product Optimization | Calls existing \`tools.shopify_bulk_feed.analyze_feed\` for Shopify catalog audits and displays optional review-only AI reports produced by \`tools/shopify_ai_copy.py\` |
| Merchant Feed Health | Calls existing \`tools.merchant_feed_diagnostics.audit\` and optional \`normalize_merchant_products\` with an uploaded processed-product status JSON |
| Approval Queue | Stages only approved **local feed text fields** with verified input, per-product approval, hash-based source checks, downloadable approval manifest and corrected TSV preview |
| Activity | Current Streamlit session staging/approval history, plus references to existing CLI tools; not a persistent log or live scheduler |

## Safety

- No live Shopify or Merchant API writes, AI inference, paid API calls, or background scheduling are performed inside the dashboard.
- Staged changes are restricted to title, description, link, image_link, brand, gtin, and mpn — not price, availability, product IDs or stock.
- Downloadable corrected feeds require every staged record to be explicitly approved; approvals reset on a changed source input. Neither a downloaded file nor an approval checkbox authorizes publication.
- AI copy remains review-only and cannot directly be published to Shopify from this interface; any live Shopify writes must follow the separate approved Shopify skill workflow.
- User uploads are processed in memory and temporary files and are not written to the repository. The dashboard host may have access to those uploads. Don't deploy the app publicly with sensitive merchant data without authentication and appropriate data controls.
- Maximum uploaded file size: 5 MB per file; maximum 5,000 feed items or products. For larger catalogs, use CLI tools.
- The synthetic product names, offers, issues and Merchant API statuses are fictional.

## Offline tests

```bash
python -m unittest tests.test_operations_dashboard
python -m compileall -q dashboard
```

CI: \`.github/workflows/operations-dashboard-tests.yml\`.

## Deploying

This repository ships Streamlit source code, **not a hosted dashboard**. You can run it locally or deploy to a private Streamlit-compatible host. Keep demo mode enabled for portfolio demonstrations. Live store connections, persistent role-based approvals and job-history ingestion would require a separately reviewed implementation.
