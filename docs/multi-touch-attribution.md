# Customer-journey multi-touch attribution

This is a **working offline, rule-based attribution engine**, not a claim that cross-platform ad APIs provide customer-level journeys. It calculates explicit first-touch, last-touch, linear, position-based (40/20/40), and time-decay credit on already joined, pseudonymous touchpoints and conversions. It is descriptive, **not incrementality or causal measurement**.

## Required data inputs for genuine journey-level attribution

Two CSVs are required. They must use a **consistent, legitimately obtained pseudonymous customer_id** and include touchpoints actually observed before each conversion. The tool does not derive customer identities or stitch devices.

**Touchpoints CSV** — one row per observed interaction:

| Column | Meaning |
| --- | --- |
| `touchpoint_id` | Unique, stable interaction ID (deduplication) |
| `customer_id` | Pseudonymous person/customer ID matched to conversions using a lawful, documented identity resolution method |
| `channel` | Normalized channel (e.g., Paid Search, Paid Social, Email, Organic) |
| `occurred_at` | Observed event timestamp, ISO-8601 with explicit timezone (e.g., `2026-01-01T10:00:00Z`) |

**Conversions CSV** — one row per **unique** order/conversion:

| Column | Meaning |
| --- | --- |
| `conversion_id` | Unique stable order or conversion ID; prevents duplicate conversion credit |
| `customer_id` | The **same pseudonymous ID namespace** as touchpoints |
| `converted_at` | Conversion timestamp with timezone |
| `revenue` | Nonnegative conversion revenue in currency units (maximum two decimal places); keep one currency per report |

**Critical upstream requirements:** source event collection and consent/authorization; reliably captured clicks, landing visits, and other defined touchpoints; persistent first-party identity or authorized login mapping connecting touchpoints to orders; documented channel taxonomy; consistent timezones and currency; deduplication of clicks/orders; coverage and reporting-window checks; and explicit policies on refunds, partial orders, ad blockers, lost identifiers, consent withdrawal, cross-device gaps, and anonymous visits. Identity mapping must be performed upstream under applicable privacy rules. Do not upload raw email addresses, phone numbers, or customer PII to this public repository.

Google Ads and Meta Ads campaign-summary APIs commonly provide **aggregated** statistics and platform-attributed conversions, *not* a portable table of all user-level touchpoints tied to Shopify orders. Klaviyo activity and Shopify order exports alone are also insufficient for complete cross-channel identity reconstruction. Never treat a cross-platform spend/revenue join as customer-journey multi-touch attribution.

## How to run

```bash
python3 tools/multi_touch_attribution.py \
  --touchpoints examples/attribution_touchpoints.csv \
  --conversions examples/attribution_conversions.csv \
  --model linear --lookback-days 30 \
  --output /tmp/multi_touch_report.json

python3 -m unittest tests.test_multi_touch_attribution -v
```

Models: `first_touch`, `last_touch`, `linear`, `position_based`, `time_decay`. Time decay defaults to a seven-day half-life, configurable with `--half-life-days`. The lookback window defaults to 30 days, including touches exactly at the boundary and at the conversion timestamp. Only matching customer IDs receive conversion credit. Events after conversion are excluded.

The JSON output provides per-order audit status, per-touchpoint fractional conversion credit and attributed revenue, channel totals, and explicit unattributed conversions/revenue. Per-order cents are allocated using largest-remainder rounding so revenue is conserved. Touchpoints without a linked conversion do not create revenue.

## Interpretation and limits

- **Attribution model choice is a business assumption**, not a discovery of actual causal contribution. Compare multiple models and validate against experiments when possible.
- The engine runs on the **touchpoints actually provided**; missing impressions, offline interactions, anonymous visitors, deleted identifiers, identity gaps, and cross-device activity affect results. It does not solve or conceal those gaps.
- It does not infer anonymous-to-known identity, implement tracking pixels, collect data from APIs, fetch ad costs, calculate incremental lift, or deduplicate orders across multiple source systems. Prepare and validate inputs upstream.
- Revenue is allocated once for each conversion with a qualifying touchpoint. Unmatched conversions remain **unattributed** rather than being redistributed across channels. Conversion IDs must be unique. Refunds and return adjustments require an explicitly defined upstream net-revenue policy.
- A path matched by customer ID is only as defensible as the upstream identity resolution and consent. Use minimum necessary data, retention controls, and access restrictions.
- All example rows are **synthetic**. No personal/customer or employer data is committed. Validate your pipelines before calling a live report multi-touch attribution.
