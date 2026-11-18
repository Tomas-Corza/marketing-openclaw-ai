# Example attribution channels and optional API credential setup

This guide accompanies the **synthetic public dashboard**, not a live multi-platform connector. The dashboard needs **no credentials**. To inspect it locally:

```bash
python3 -m pip install -r dashboard/requirements.txt
streamlit run dashboard/app.py
```

Select **Ad Attribution**. Its fixtures are [GA4 events](../examples/dashboard/attribution_events.csv) and [Shopify orders](../examples/dashboard/attribution_orders.csv). All data, order values and journeys are fictional.

## Sources, identifiers, and connection status

| Example channel | What is represented in the demo | Optional API/authorization for additional reporting | Current attribution integration |
| --- | --- | --- | --- |
| Meta Ads | Synthetic paid-social storefront visits | Meta Marketing API system-user/user access token and permitted ad account | Event-level GA4/Shopify CSV only; no Meta Ads API adapter |
| Google Ads | Synthetic paid-search storefront visits | Google Ads API OAuth credentials, developer token, and customer account ID | Event-level GA4/Shopify CSV only; no Google Ads API adapter |
| Microsoft Ads (Bing) | Synthetic Bing paid-search visits | Microsoft Advertising API OAuth access/refresh flow, developer token, account/customer IDs | Event-level GA4/Shopify CSV only; no Microsoft Ads API adapter |
| Etsy Referral | Synthetic visitors referred from Etsy to the Shopify site | Etsy Open API OAuth credentials **only if** implementing a separately authorized Etsy reporting connector | Referrals only; not Etsy checkout/order attribution |
| Amazon Referral | Synthetic visitors referred from Amazon to the Shopify site | Appropriate Amazon Ads or Selling Partner API authorization **only if** building that separately scoped reporting integration | Referrals only; not Amazon checkout/order attribution |
| ChatGPT Referral | Synthetic visitors arriving at Shopify from a ChatGPT referrer | No ChatGPT API key is needed or sufficient to read ChatGPT referral journeys; track observable, consented referral/UTM signals in GA4 | Referrals only; no access to ChatGPT conversations or user accounts |
| Google Organic | Synthetic Google organic-search visits | No ad API key is needed for GA4-observed organic traffic; Search Console API authorization is optional for aggregate search reporting | Event-level GA4/Shopify CSV only |
| GA4 BigQuery and Shopify | Consent-aware event observations and order/purchase validation | Authorized Google Cloud credentials and Shopify Admin API credentials/scopes for a **future secure export/ingestion workflow** | Existing offline CSV join, **not** direct API connectivity |

**Important distinction:** Marketing platform APIs typically provide campaign performance reports, not a universal person-level sequence of every ad impression or visit. An API key does not establish an attributable customer journey. The working pipeline allocates revenue only to observed, consented storefront visits whose GA4 purchase transaction matches a Shopify order. It does not merge Etsy/Amazon marketplace orders into Shopify conversions.

## Add or remove a channel from the *public demo*

- **Add:** Edit `examples/dashboard/attribution_events.csv` and create a unique `event_id` row with the new channel name, a fictional `user_pseudo_id`, `event_name=page_view` or `session_start`, ISO-8601 timestamp, and `analytics_storage=Yes`. To assign revenue, also include a `purchase` event with a transaction ID matching a row in `examples/dashboard/attribution_orders.csv`, using the same pseudonymous ID and a purchase timestamp within 24 hours of the order.
- **Remove:** Delete only that channel's visit rows from the synthetic events CSV. Keep purchase/order rows if you want to demonstrate conversions with no eligible touchpoints.
- **Rename:** Use consistent channel labels across events. `channel` is a classification, not a credential or proof that the advertising platform was connected.
- **Verify:** Run `python3 -m unittest discover -s tests -p 'test_attribution_dashboard.py' -v`. Adjust the exact seven-channel test assertions if you intentionally change the demonstration channels.

You never need an API key to add/remove **synthetic** channels.

## Configure optional *future* live reporting credentials privately

These names are **illustrative configuration conventions, not inputs consumed by the current attribution dashboard or pipeline**. Do not expect placing secrets in a file to activate integrations.

1. Decide which additional API-powered reporting connector you actually need, and obtain the relevant provider's permission/approval and least-privilege scopes. For Google, Microsoft, Etsy, and many Amazon APIs, the proper setup uses **OAuth or other signed credentials**, not one static API key.
2. In a secure local environment or secret manager, supply only the credentials for connectors you have actually implemented and authorized. Example placeholder names:

```dotenv
# EXAMPLE ONLY — do not commit real values; no existing code reads these variables.
META_ADS_ACCESS_TOKEN=
META_ADS_ACCOUNT_ID=
GOOGLE_ADS_DEVELOPER_TOKEN=
GOOGLE_ADS_CLIENT_ID=
GOOGLE_ADS_CLIENT_SECRET=
GOOGLE_ADS_REFRESH_TOKEN=
GOOGLE_ADS_CUSTOMER_ID=
MICROSOFT_ADS_DEVELOPER_TOKEN=
MICROSOFT_ADS_CLIENT_ID=
MICROSOFT_ADS_REFRESH_TOKEN=
MICROSOFT_ADS_ACCOUNT_ID=
ETSY_CLIENT_ID=
ETSY_OAUTH_ACCESS_TOKEN=
AMAZON_ADS_CLIENT_ID=
AMAZON_ADS_CLIENT_SECRET=
AMAZON_ADS_REFRESH_TOKEN=
GOOGLE_CLOUD_PROJECT_ID=
SHOPIFY_SHOP_DOMAIN=
SHOPIFY_ADMIN_ACCESS_TOKEN=
```

3. Add provider-specific code that obtains/refreshes OAuth tokens as necessary, requests only permitted reports, handles failures and quotas, and maps resulting **aggregate** campaign reports to a separately defined reporting model. Keep campaign-report data separate from individual GA4 journeys unless you have valid, consented identifiers.
4. Store secrets outside Git. A locally sourced `.env` file must be gitignored; on Streamlit Community Cloud, use **App settings → Secrets** only when a live integration is explicitly built and reviewed. Do not make secret values downloadable or visible in a public page.
5. To **disable a real integration**, switch it off in its connector-specific configuration, remove its secret(s) from the secure store, revoke the token or OAuth grant at the provider, and rotate shared credentials when appropriate. Removing a token prevents calls but does not necessarily remove already collected data; apply retention/deletion policies separately.
6. To **add a new live channel**, implement and test its connector, document permissions/scopes and field mappings, and introduce explicit feature gating and audit logs. The current public demo deliberately performs zero live platform calls.

For the actual supported CSV schemas and attribution logic, see [GA4–Shopify pipeline](shopify-ga4-bigquery-pipeline.md) and [multi-touch engine](multi-touch-attribution.md). All sample CSV rows are fictional, and no credentials or personally identifiable customer information belong in GitHub.
