# Shopify + GA4 BigQuery attribution pipeline

This is a **working offline preparation pipeline** that converts authorized GA4 BigQuery event exports and Shopify order exports into linked journeys for the rule-based multi-touch attribution engine. It does not configure or connect a live store, Google Analytics, or BigQuery automatically. It attributes **observed same-browser journeys**, not every marketing touchpoint across devices.

## Required setup and data

1. Have authorized administrative access to a Shopify store and its GA4 property and BigQuery project. Configure GA4 event-level BigQuery daily export, legal notice and applicable consent controls. Historic events cannot be backfilled where they were never recorded.
2. Verify the GA4 `purchase` event includes `ecommerce.transaction_id` **exactly equal to your Shopify exported `order_id`**. Shopify order `id`, `name`, checkout token, and human-facing order number can differ. Verify the intended identifier in a development store. Never assume the IDs already match.
3. Query GA4 using [the SQL template](ga4_bigquery_export.sql), replacing `YOUR_PROJECT.analytics_PROPERTY_ID` and setting `@start_date` and `@end_date` in `YYYYMMDD` format. Include the desired lookback period. The query uses event-level source and medium fields, not the original first-user acquisition source, and deliberately drops unclassifiable/direct traffic. Review channel classification for your implementation. It includes only events with GA4 `analytics_storage = 'Yes'`.
4. Export a Shopify orders CSV with unique `order_id`, `converted_at`, `revenue`, and `currency`. Define a consistent revenue basis (taxes, shipping, refunds, canceled orders) and choose one currency for each run. Run the processing locally or in an authorized secure cloud environment.
5. The pipeline joins a Shopify order to a GA4 `purchase` event **only if** transaction IDs match, the purchase is within 24 hours of the Shopify conversion time, and precisely one consented GA4 `user_pseudo_id` is associated with that order. Ambiguous orders get no credit. Earlier consented events under that browser identifier are eligible for the rule-based models.

## CSV schemas

| CSV | Required fields |
| --- | --- |
| GA4 | `event_id`, `user_pseudo_id`, `event_name`, `occurred_at`, `channel`, `transaction_id`, `analytics_storage` |
| Shopify | `order_id`, `converted_at`, `revenue`, `currency` |

Timestamps require ISO-8601 UTC/offsets. Each event and order ID must be unique. Only GA4 `page_view` and `session_start` rows with recognized channels count as touchpoints. GA4 `purchase` rows are identity/order bridges, **not** attribution touchpoints.

## Run with synthetic fixtures

```bash
python3 tools/shopify_ga4_pipeline.py \
  --ga4-events examples/ga4_bigquery_events.csv \
  --shopify-orders examples/shopify_attribution_orders.csv \
  --model linear --lookback-days 30 \
  --output /tmp/shopify-ga4-attribution.json

python3 -m unittest discover -s tests -p 'test_shopify_ga4_pipeline.py' -v
```

The output includes attributed and unmatched conversion counts; its `pipeline_audit` section also reports unmatched Shopify orders and mismatched/ambiguous purchase mappings. Orders without verifiable matches are not assigned conversion credit. Sample data is synthetic.

## Limits and security

- GA4 browser identifiers do not, by themselves, link cross-device behavior. Consent signals and privacy-law obligations must be respected; do not reconstruct visitors using email, IP addresses, fingerprints, or unauthorized identity resolution.
- The SQL template uses an event hash as an ID: duplicate event keys can collide and must be audited before running on real exports. Source-level identity/event instrumentation and classification should be tested in a development store.
- Customer journeys and BigQuery raw exports are potentially sensitive. Keep credentials, raw exports, private IDs, and customer data out of public GitHub. Apply access controls, retention and deletion policies.
- This is **rule-based credit allocation**, not an estimate of causal advertising lift. Blocked consent, offline contacts, missing UTMs, impressions, cross-device behavior, and missing `transaction_id` limit coverage. No platform API creates missing interactions.
- The pipeline does not automatically provision Shopify Web Pixels, the GA4 tag, BigQuery permissions, Shopify order export, or credentials. Authorized configuration and end-to-end live validation are separate tasks.

References: [GA4 BigQuery export schema](https://support.google.com/analytics/answer/7029846), [GA4 BigQuery queries](https://developers.google.com/analytics/bigquery/basic-queries), [Shopify Pixels](https://help.shopify.com/en/manual/promoting-marketing/pixels/), [Shopify GTM custom pixel tutorial](https://help.shopify.com/en/manual/promoting-marketing/pixels/custom-pixels/gtm-tutorial).
