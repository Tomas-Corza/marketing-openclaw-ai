# Social Media Behavior Monitor — integration contract

This is a **platform-neutral analytics layer**, not a preconnected social listening or scraping service.

## Data contract

Input: UTF-8 CSV containing one row per piece of content, per platform and observation date range.

Required columns:
- `platform` — source platform (e.g., instagram, youtube, tiktok, linkedin)
- `content_id` — source content identifier; not a personal-user identifier
- `published_at` — ISO 8601 timestamp or YYYY-MM-DD
- `impressions`, `likes`, `comments`, `shares`, `saves`, `clicks` — nonnegative integers; blank means unknown

Optional columns: `content_type`, `topic`, `campaign`, `views`, `reach`, `source_url`.

Metrics: interactions = likes + comments + shares + saves; engagement / impression = interactions ÷ impressions (only where the platform provides a comparable impression denominator). Click / impression = clicks ÷ impressions. Aggregated rates are ratios of summed numerators to summed denominators, not averages of row rates. A missing numeric value is **unknown**, not zero.

For cross-platform comparisons, report each platform separately; metric definitions and availability vary. These counts represent content-level observations, not unique-user behavior. Engagement cannot establish individual motivations or predict individual decisions.

## Connector design

Authorized future adapters should implement:
`fetch(start_at, end_at, account_ids, credentials) -> iterable[dict]`
and `normalize(raw_record) -> dict` matching the data contract.

See `tools/social_behavior_connector.py` for the abstract adapter interface and CSV implementation. API-specific adapters should live in `connectors/<platform>.py` and be tested against that platform's documented data fields.

**Not included:** OAuth flow, refresh-token storage, API endpoints, webhook receiver, schedule, or scraping. Add only after selecting a provider and confirming scopes and rules. Never commit secrets, tokens, private exports or user-level data.

## Usage

```bash
python3 tools/social_behavior_monitor.py --input examples/social_behavior_sample.csv
python3 tools/social_behavior_monitor.py --input examples/social_behavior_sample.csv --output report.json
```

No external packages are required. Input validation fails on negative or invalid counts, duplicate platform/content IDs, and missing required fields. Reports are JSON and describe only observed data.

## Integrating a new platform

1. Review the provider API documentation and approve account scopes and permissible data.
2. Implement an adapter to fetch authorized analytics with pagination, retries, and backoff.
3. Normalize provider metrics without replacing unavailable values with zero.
4. Validate sample exports; check attribution, reporting window, and metric definitions.
5. Store secrets outside GitHub, document deletion and retention, and obtain permission for any automation.
