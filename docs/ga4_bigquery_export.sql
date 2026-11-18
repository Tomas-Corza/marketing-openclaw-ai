-- BigQuery Standard SQL template for event-level GA4 web analytics.
-- Replace YOUR_PROJECT.analytics_PROPERTY_ID with the actual project and GA4 export dataset.
-- Supply named query parameters @start_date and @end_date as YYYYMMDD strings.
-- The start date must include the intended attribution lookback period.
-- IMPORTANT: Ensure GA4 ecommerce.transaction_id matches the Shopify order ID export.
WITH raw AS (
  SELECT event_name, event_timestamp, user_pseudo_id,
    privacy_info.analytics_storage AS analytics_storage,
    COALESCE(ecommerce.transaction_id, '') AS transaction_id,
    collected_traffic_source.manual_source AS source,
    collected_traffic_source.manual_medium AS medium,
    collected_traffic_source.gclid AS gclid,
    (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location' LIMIT 1) AS page_location,
    (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id' LIMIT 1) AS ga_session_id,
    event_bundle_sequence_id
  FROM `YOUR_PROJECT.analytics_PROPERTY_ID.events_*`
  WHERE _TABLE_SUFFIX BETWEEN @start_date AND @end_date
    AND event_name IN ('page_view', 'session_start', 'purchase')
    AND privacy_info.analytics_storage = 'Yes'
    AND user_pseudo_id IS NOT NULL
), prepared AS (
 SELECT *,
    CASE
      WHEN event_name = 'purchase' THEN ''
      WHEN LOWER(COALESCE(medium, '')) = 'email' THEN 'Email'
      WHEN LOWER(COALESCE(medium, '')) IN ('cpc','ppc','paid','paidsearch','paid_search')
        OR gclid IS NOT NULL
        THEN CASE
          WHEN REGEXP_CONTAINS(LOWER(COALESCE(source, '')), r'(facebook|instagram|meta|tiktok|pinterest)')
          THEN 'Paid Social' ELSE 'Paid Search' END
      WHEN LOWER(COALESCE(medium, '')) IN ('social','social-network','social-media') THEN 'Organic Social'
      WHEN LOWER(COALESCE(medium, '')) = 'organic' THEN 'Organic Search'
      WHEN LOWER(COALESCE(medium, '')) = 'referral' THEN 'Referral'
      ELSE ''
    END AS channel
 FROM raw
)
SELECT
  TO_HEX(SHA256(CONCAT(
    COALESCE(user_pseudo_id,''),'|',CAST(event_timestamp AS STRING),'|',event_name,'|',
    CAST(COALESCE(ga_session_id,0) AS STRING),'|',
    CAST(COALESCE(event_bundle_sequence_id,0) AS STRING),'|',
    COALESCE(page_location,''),'|',transaction_id
  ))) AS event_id,
  user_pseudo_id, event_name,
  FORMAT_TIMESTAMP('%Y-%m-%dT%H:%M:%E6SZ', TIMESTAMP_MICROS(event_timestamp),'UTC') AS occurred_at,
  channel, transaction_id, analytics_storage
FROM prepared
WHERE event_name = 'purchase' OR channel != ''
