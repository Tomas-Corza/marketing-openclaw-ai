# Streamlit Dashboard — Deployment & Maintenance

This is the **maintainer/developer guide** for the existing public Marketing OpenClaw AI dashboard, not copy for the portfolio landing page.

**Live app:** https://marketing-openclaw-ai-ecommerce-operations-dashboard.streamlit.app/  
**GitHub repository:** https://github.com/Tomas-Corza/marketing-openclaw-ai

The public app uses **fictional, synthetic-only data**. No live Shopify store, GA4 property, Google Merchant Center, ad account, inbox, or marketplace account is connected.

## Current configuration

| Setting | Configuration |
| --- | --- |
| Repository | `Tomas-Corza/marketing-openclaw-ai` |
| Deployment branch | `main` |
| Public entrypoint | `dashboard/public_app.py` |
| Dependencies | `dashboard/requirements.txt` |
| Synthetic catalog and attribution fixtures | `examples/dashboard/` |
| Local development entrypoint | `dashboard/app.py` — **do not use for the public deployment** |

The public entrypoint sets `OPENCLAW_PUBLIC_DEMO=1` before running the dashboard, keeping merchant upload controls disabled.

## Public dashboard features

The six views are **Overview**, **Product Optimization**, **Merchant Feed Health**, **Ad Attribution**, **Approval Queue**, and **Activity**.

The attribution view uses fictional GA4 event observations matched to fictional Shopify orders and lets visitors compare five rule-based attribution models: first touch, last touch, linear, position-based, and time decay. It shows credited revenue, unmatched orders, and observable journeys.

### Example attribution channels

| Example input | Meaning in the demo |
| --- | --- |
| Meta Ads | Fictional paid social visits |
| Google Ads | Fictional paid search visits |
| Microsoft Ads (Bing) | Fictional Bing paid search visits |
| Etsy Referral | Fictional referrals from Etsy to Shopify, **not Etsy order data** |
| Amazon Referral | Fictional referrals from Amazon to Shopify, **not Amazon order data** |
| ChatGPT Referral | Fictional observed website referrals, **not ChatGPT user-account data** |
| Google Organic | Fictional organic Google search visits |

The dashboard does **not** read live ad platform APIs. Attribution credit is descriptive, not a causal advertising-effectiveness estimate or complete cross-device tracking.

For setup details, see [example channels and credential management](example-attribution-channels-and-credentials.md), [Shopify + GA4 pipeline](shopify-ga4-bigquery-pipeline.md), and [dashboard development guide](../dashboard/README.md).

## Updating the existing deployment

1. Make changes on a GitHub branch and run the relevant tests.
2. Open and review a pull request; merge approved changes into `main` after required checks pass.
3. Streamlit Community Cloud usually redeploys when the configured branch changes.
4. Open the [live dashboard](https://marketing-openclaw-ai-ecommerce-operations-dashboard.streamlit.app/) and confirm all six tabs load, the synthetic-data notice appears, and no upload controls are present.
5. If updates are missing or the app fails to start, sign in at [Streamlit Community Cloud](https://share.streamlit.io/), inspect the existing app's deployment settings and logs, verify `main` and `dashboard/public_app.py`, then reboot the app if necessary.

Do **not** create a second Streamlit application just to publish code changes. A successful GitHub Actions run or merged pull request does not by itself verify the hosted app is functioning.

## Preview and test locally

From the cloned repository root:

```bash
python3 -m pip install -r dashboard/requirements.txt
streamlit run dashboard/public_app.py
```

Run automated checks:

```bash
python3 -m unittest discover -s tests -p 'test_operations_dashboard.py' -v
python3 -m unittest discover -s tests -p 'test_attribution_dashboard.py' -v
python3 -m unittest discover -s tests -p 'test_multi_touch_attribution.py' -v
python3 -m unittest discover -s tests -p 'test_shopify_ga4_pipeline.py' -v
python3 -m compileall -q dashboard
```

To process merchant-authorized catalog/feed uploads **locally**, use `streamlit run dashboard/app.py` and select the appropriate non-demo mode. Do not publish the upload-enabled entrypoint as the public app.

## Change example attribution channels

Edit `examples/dashboard/attribution_events.csv` to add, remove, or rename fictional channel events. Each event needs a unique ID, an appropriate pseudonymous browser identifier, and an ISO-8601 timestamp with timezone. To show attributed purchases, GA4 purchase transaction IDs must match `order_id` in `examples/dashboard/attribution_orders.csv`; maintain matching consent and timeline examples.

Run the attribution tests again, and update any assertions tied to the original seven channels.

**No API keys are needed for the synthetic demo.** To enable a live reporting source, a separately implemented connector must be authorized, tested and configured with secure credentials. See [channel and credential configuration](example-attribution-channels-and-credentials.md). Adding a token does not automatically connect an ad platform.

## Portfolio link

Use the actual existing dashboard URL:

```html
<a href="https://marketing-openclaw-ai-ecommerce-operations-dashboard.streamlit.app/"
   target="_blank" rel="noopener noreferrer">
  Explore the Marketing OpenClaw AI Demo
</a>
```

Suggested description: “Explore a synthetic demonstration of Shopify operations, product-feed diagnostics, and customer-journey attribution across seven example marketing channels.”

## Security and operating limits

- No live Shopify, GA4, BigQuery, Meta Ads, Google Ads, Microsoft Ads, Gmail, Merchant Center, Etsy, Amazon, or ChatGPT account connections are performed by the public dashboard.
- The demonstration does not accept uploads of customer data. Any local feed approvals affect only a downloadable preview; they cannot publish changes or refunds.
- Never commit real API secrets, visitor-level exports, or customer information to the public GitHub repository. Any real deployment requires authentication, provider permissions, privacy controls and secure data storage.
- Attribution cannot infer unobserved activity, identify visitors across devices, or prove causal advertising lift. Unmatched conversions are kept unmatched.

## Official Streamlit documentation

- [Deploy your app](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
- [File organization](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization)
