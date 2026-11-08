# TOOLS.md — Integration notes (example)

This is a public template, not a record of installed or working integrations.

## Optional integration categories

- E-commerce analytics (for example, Shopify API)
- Email marketing analytics (for example, Klaviyo API)
- Reporting exports (for example, Google Sheets API)
- Public competitor and search research\n- Social-platform content analytics (authorized APIs or exports; not connected by default)

For each integration, document prerequisites, permissions, environment-variable names, rate limits, error handling, and data-retention policies. Put credentials only in locally managed secret storage. Never commit `.env`, service-account JSON keys, OAuth tokens, or real customer exports.

No integrations are enabled by this file alone.

## Marketing Analysis Tools

### Jobs-to-be-Done Analysis
- Skill: `skills/jtbd-analysis/SKILL.md`
- Script: `jtbd/analyze.py`
- Purpose: Compare marketing messages using Jobs-to-be-Done motivations.
- Input: CSV containing variant, job, delivered, clicks.

### Email Marketing Analytics
- Skill: `skills/email-analytics/SKILL.md`
- Script: `tools/email_analytics.py`
- Purpose: Analyze email campaign engagement and revenue.
- Input: CSV containing campaign, sent, clicks, orders, revenue.

### Social Media Behavior Monitor
- Skill: `skills/social-behavior-monitor/SKILL.md`
- Script: `tools/social_behavior_monitor.py`
- Connector contract: `tools/social_behavior_connector.py`
- Schema and setup: `docs/social-behavior-monitor.md`
- Example: `examples/social_behavior_sample.csv`
- Purpose: Summarize authorized social media engagement at the content level.
- Input: Normalized CSV; platform-specific APIs require separately implemented and approved adapters.

## Execution Guidelines

- Run scripts from the project root directory.
- Only process authorized datasets.
- Use synthetic data for demonstrations.
- Never invent marketing performance results.
- Explain findings in clear, nontechnical language.
- Do not modify live campaigns without approval.
