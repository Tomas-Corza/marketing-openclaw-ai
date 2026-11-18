# AI E-Commerce Operations Dashboard

A Streamlit control center for the Marketing OpenClaw AI repository, designed for **offline demonstrations and controlled human review**. Upload merchant-authorized inputs or use the bundled synthetic fixtures. The dashboard does not create live Shopify, Google Merchant, or OpenAI API connections.

## Launch

From the repository root with Python 3.10+:

```bash
python -m pip install -r dashboard/requirements.txt
streamlit run dashboard/app.py
```

The synthetic demonstration dataset loads automatically. No API credentials are needed. Its attribution view includes seven fictional channels: Meta Ads, Google Ads, Microsoft Ads (Bing), Etsy Referral, Amazon Referral, ChatGPT Referral and Google Organic.

## Six dashboard views

| View | Capabilities |
| --- | --- |
| Overview | Catalog/feed KPI cards, counts of issues and pending work |
| Product Optimization | Calls existing `tools.shopify_bulk_feed.analyze_feed` for Shopify catalog audits and displays optional review-only AI reports produced by `tools/shopify_ai_copy.py` |
| Merchant Feed Health | Calls existing `tools.merchant_feed_diagnostics.audit` and optional `normalize_merchant_products` with an uploaded processed-product status JSON |
| Approval Queue | Stages only approved **local feed text fields** with verified input, per-product approval, hash-based source checks, downloadable approval manifest and corrected TSV preview |
| Ad Attribution | Interactive synthetic GA4 + Shopify customer-journey matching with five rule-based attribution models, order audit, model comparison, channel credit, and downloadable synthetic JSON. Requires matched event and order IDs; no live API access. |
| Activity | Current Streamlit session staging/approval history, plus references to existing CLI tools; not a persistent log or live scheduler |

## Safety

- No live Shopify, GA4, BigQuery, Merchant or advertising API calls, Shopify writes, AI inference, paid API calls, or background scheduling are performed inside the dashboard.
- The public attribution tab is **synthetic-only**, with no customer uploads. Rule-based credit allocation is not a claim of causal advertising impact or complete cross-device coverage.
- Staged changes are restricted to title, description, link, image_link, brand, gtin, and mpn — not price, availability, product IDs or stock.
- Downloadable corrected feeds require every staged record to be explicitly approved; approvals reset on a changed source input. Neither a downloaded file nor an approval checkbox authorizes publication.
- AI copy remains review-only and cannot directly be published to Shopify from this interface; any live Shopify writes must follow the separate approved Shopify skill workflow.
- User uploads are processed in memory and temporary files and are not written to the repository. The dashboard host may have access to those uploads. Don't deploy the app publicly with sensitive merchant data without authentication and appropriate data controls.
- Maximum uploaded file size: 5 MB per file; maximum 5,000 feed items or products. For larger catalogs, use CLI tools.
- The synthetic product names, offers, issues and Merchant API statuses are fictional.

## Synthetic advertising attribution walkthrough

Choose the **Ad Attribution** tab. Switch between first-touch, last-touch, linear, position-based, and time-decay credit models, change the lookback window, compare credited revenue by channel, inspect a matched order's journey, and download the synthetic JSON report.

The new tab uses `dashboard/attribution_view.py` and the same `tools/shopify_ga4_pipeline.py` and `tools/multi_touch_attribution.py` code as the offline CLI. The dashboard fixtures in `examples/dashboard/attribution_events.csv` and `examples/dashboard/attribution_orders.csv` are fictional, and the tab does not accept real customer datasets.

To add or remove sample channels, edit the attribution events CSV. See [channel and credential setup](../docs/example-attribution-channels-and-credentials.md). No ad-platform API credentials are used in this demo.

See [Shopify–GA4 BigQuery setup](../docs/shopify-ga4-bigquery-pipeline.md) and [Multi-touch data requirements](../docs/multi-touch-attribution.md). A real deployment requires permissioned event collection, accurate order-ID matching, and privacy controls; nothing is connected automatically.

## Offline tests

```bash
python -m unittest discover -s tests -p 'test_operations_dashboard.py'
python -m unittest discover -s tests -p 'test_attribution_dashboard.py'
python -m compileall -q dashboard
```

CI: `.github/workflows/operations-dashboard-tests.yml`.

## Public Streamlit dashboard

The public, synthetic-only showcase has been deployed at [Marketing OpenClaw AI E-Commerce Operations Dashboard](https://marketing-openclaw-ai-ecommerce-operations-dashboard.streamlit.app/). The GitHub deployment target is `main` with `dashboard/public_app.py` as the entrypoint. This entrypoint forces synthetic demonstration data and disables merchant uploads. Do **not** use the upload-enabled `dashboard/app.py` for public deployment.

See [Deployment & Maintenance](../docs/streamlit-community-cloud-deployment.md) for updating or troubleshooting this existing app. A GitHub merge does not itself confirm a successful Streamlit redeployment. Actual deployment settings and uptime must be checked in Streamlit Community Cloud.

Live store connections, secure data uploads, persistent role-based approvals and job-history ingestion would require a separately reviewed implementation.
