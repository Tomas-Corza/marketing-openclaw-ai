---
name: email-analytics
description: Analyze email marketing campaigns, engagement, and revenue performance from CSV files.
---

# Email Marketing Analytics

Use this skill when the user requests email campaign performance analysis.

## Supported metrics

- Email click rate
- Revenue per email sent
- Order counts
- Campaign comparisons

## Procedure

1. Confirm the CSV contains:
   campaign, sent, clicks, orders, revenue
2. Confirm the dataset is authorized for analysis.
3. Run from the project root:

   python3 tools/email_analytics.py <csv_file>

4. Explain the results in plain language.
5. Identify campaigns with stronger observed performance.
6. Recommend follow-up experiments.

## Rules

- Never invent campaign results.
- Do not claim causal improvements from observational data.
- Do not access confidential business data without authorization.
- Request approval before modifying or sending campaigns.
