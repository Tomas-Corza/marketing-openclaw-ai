# Marketing OpenClaw AI

**A customizable AI-powered marketing assistant built on the OpenClaw ecosystem.**

**Developed by Tomas Corza | Growth Marketing & Analytics**

## Overview

Marketing OpenClaw AI is a marketing-focused AI assistant framework designed to support digital marketing analysis, reporting, experimentation, and automation.

The project is based on an AI assistant implementation previously used in a real-world marketing environment. Its architecture and workflows have been adapted into a reusable, public-facing project that can be configured for different businesses, marketing platforms, and analytical requirements.

The original implementation demonstrated the practical application of AI-assisted marketing workflows. This repository provides a generalized version, including agent configuration files, independently runnable Python analysis tools, and skill definitions.

**The framework has a history of practical use, but each new implementation requires configuration, integration, and testing for its intended environment.**

## Capabilities

### Jobs-to-be-Done (JTBD) Marketing Analysis

Analyze marketing messages based on the customer motivations they address.

- Compare messaging variants across different customer jobs.
- Calculate and rank email click-through rates.
- Identify the highest-performing observed messaging approach.
- Support value proposition development and marketing experimentation.
- Distinguish observed performance differences from statistically validated conclusions.

**Included:** `jtbd/analyze.py` and `skills/jtbd-analysis/SKILL.md`

### Email Marketing Analytics

Analyze email campaign performance using structured campaign data.

- Measure campaign engagement and click-through rates.
- Calculate revenue per email sent.
- Compare campaign performance.
- Report orders and revenue.
- Summarize findings in accessible, nontechnical language.

**Included:** `tools/email_analytics.py` and `skills/email-analytics/SKILL.md`

### Social Media Behavior Monitor (API-ready)

Analyze authorized social media content-level engagement across platforms through a normalized data model.

- Summarize likes, comments, shares, saves, clicks, and impressions (when available).
- Compare topics and content formats within each platform.
- Handle missing metrics and show metric coverage, rather than assume zero.
- Produce machine-readable JSON analysis for reports and downstream AI interpretation.
- Start offline with a synthetic CSV example; add authorized platform adapters later.

**Included:** `skills/social-behavior-monitor/SKILL.md`, `tools/social_behavior_monitor.py`, `tools/social_behavior_connector.py`, `docs/social-behavior-monitor.md`.

**Status:** Offline analytics implemented. No live API connections, monitoring schedule, or scraping configured.

### Shopify Product Page Automation (API-ready)

Audit product-page content, fetch authorized Shopify product records through the GraphQL Admin API, preview proposed changes, and apply explicitly approved product title, HTML description, and SEO metadata updates.

- Offline audit with synthetic product JSON.
- Authorized Shopify read and write integration with environment-provided credentials.
- Read-before-write preview; explicit confirmation required to update.
- OpenClaw skill instructions for fact-checked, JTBD-informed content proposals.
- No live Shopify credentials, autonomous text generation, or scheduled publishing included.

**Included:** `tools/shopify_product_pages.py`, `skills/shopify-product-page-automation/SKILL.md`, `docs/shopify-product-page-automation.md`, and synthetic examples.

```bash
python3 tools/shopify_product_pages.py audit --input examples/shopify_product_sample.json
```

See [Shopify integration setup](docs/shopify-product-page-automation.md) for API configuration and the approval-first publishing workflow.

### Shopify Bulk Feed Optimization (API-ready)

Extend the Shopify product-page skill across a product catalog with a Shopify CSV export.

- Group Shopify variant rows into unique products.
- Audit titles, descriptions and custom SEO fields at catalog scale.
- Export machine-readable JSON findings and conservative metadata drafts.
- Prepare product-ID-mapped, approval-required API update manifests.
- Apply capped batches with stale-content checks and private JSONL audit logs.
- No AI-written copy or unattended product publishing by default.

**Included:** `tools/shopify_bulk_feed.py`, `docs/shopify-bulk-feed-optimization.md`, `tests/test_shopify_bulk_feed.py`, and `examples/shopify_bulk_feed_sample.csv`.

```bash
python3 tools/shopify_bulk_feed.py analyze --input examples/shopify_bulk_feed_sample.csv --output /tmp/shopify-audit.json
```

See [Bulk Shopify feed guide](docs/shopify-bulk-feed-optimization.md).

### AI-Powered Shopify Catalog Copy Generation (review-only)

Generate proposed product-page titles, descriptions and SEO metadata at catalog scale using the OpenAI Responses API and verified merchant source fields. The agent produces a Jobs-to-be-Done messaging hypothesis and review notes for each product. API access and merchant authorization are required; these are **drafts only**, not autonomous publishing.

- Strict JSON output, escaped HTML, per-product errors and rate/cost caps.
- No live Shopify writes: human review and explicit approvals remain mandatory.
- Generated claims require independent verification against product facts.

**Included:** `tools/shopify_ai_copy.py`, `tests/test_shopify_ai_copy.py`, `docs/shopify-ai-copy-generation.md`.

```bash
python3 tools/shopify_ai_copy.py --input examples/shopify_bulk_feed_sample.csv --output /tmp/shopify-ai-review.json --max-products 10
```

See [AI product copy setup](docs/shopify-ai-copy-generation.md).

### Shopify Product Feed Creation (CSV → Merchant Center TSV / RSS)

Generate Google Merchant Center-style product feeds offline from authorized Shopify CSV exports.

- Convert variant-level catalog rows to stable SKU-based feed item IDs.
- Export tab-delimited TSV or RSS XML with title, description, price, inventory availability, image, product URL and identifiers.
- Reject incomplete products and export a separate machine-readable validation report.
- Support repeatable generation from fresh exports (an automated Shopify export and hosted feed are separate deployment tasks).

**Included:** `tools/shopify_feed_builder.py`, `docs/shopify-product-feed-builder.md`, `examples/shopify_merchant_feed_sample.csv`, and offline tests.

```bash
python3 tools/shopify_feed_builder.py --input examples/shopify_merchant_feed_sample.csv --store-url https://example.com --output /tmp/merchant-feed.tsv --rejects /tmp/merchant-feed-errors.json
```

See [Feed creation guide](docs/shopify-product-feed-builder.md).

### AI Agent Architecture

The project includes an OpenClaw-style configuration structure for guiding an AI assistant's behavior, analytical workflows, tool usage, and operational boundaries.

| File | Purpose |
|---|---|
| `IDENTITY.md` | Defines the assistant's identity and marketing expertise |
| `SOUL.md` | Establishes communication principles and analytical behavior |
| `AGENTS.md` | Documents operating instructions and safety constraints |
| `TOOLS.md` | Describes supported tool interfaces and potential integrations |
| `HEARTBEAT.md` | Provides a template for recurring monitoring and automation |
| `skills/` | Contains reusable marketing skill instructions |
| `jtbd/` | Contains Jobs-to-be-Done analysis tools |
| `tools/` | Contains additional marketing analysis scripts |

## Potential Integrations

The framework can be extended to work with marketing and reporting platforms, including:

- Shopify — e-commerce performance and sales analysis
- Klaviyo — email marketing performance
- Google Sheets — reporting and data exports
- Google Ads and Meta Ads — campaign performance analysis
- Public competitor research — market monitoring and competitive intelligence

These integrations require separate configuration, authorized API access, and any necessary implementation work. They are not enabled by default in this repository.

## Running the Included Analysis Tools

The included Python scripts can run independently of an OpenClaw installation.

**JTBD analysis**

```bash
python3 jtbd/analyze.py jtbd/example.csv
```

**Social media behavior analysis**

```bash
python3 tools/social_behavior_monitor.py --input examples/social_behavior_sample.csv
python3 -m unittest discover -s tests
```

**Email marketing analysis**

```bash
python3 tools/email_analytics.py tools/example_email.csv
```

The example CSV files contain synthetic demonstration data, not actual business performance results.

## Deployment and Adaptation

Marketing OpenClaw AI is derived from a previously used marketing AI assistant implementation. The public version is intended to serve as a configurable foundation for new marketing applications.

Before deploying the framework in a new environment, users should:

1. Adapt the agent instructions and skills to the intended business and marketing objectives.
2. Configure the required integrations and access permissions.
3. Test compatibility with the target OpenClaw environment.
4. Validate analytical outputs against trusted data sources.
5. Review security, privacy, and data-handling requirements.

**Previous practical use does not guarantee compatibility with every new application. Configuration and testing are required before deployment.**

## Privacy and Security

This public repository is intended to contain reusable configuration patterns, original or independently adapted analysis code, and synthetic demonstration data.

It does not include live credentials, customer information, private business reports, or original company datasets.

Users should avoid committing sensitive information and should review authorization and data-retention requirements before connecting external systems.

## Development History

The Jobs-to-be-Done AI methodology underlying this project builds on my independently developed **JTBDGPT** initiative, publicly documented in September 2024 in [*JTBDGPT: A Jobs to Be Done AI Innovation Expert*](https://www.linkedin.com/pulse/jtbdgpt-jobs-done-ai-innovation-expert-tomas-corza-ueckc/). That earlier work was subsequently adapted into broader AI-assisted marketing workflows. The 2024 article documents the JTBD AI initiative, not the creation date of this entire OpenClaw framework.

## Project Purpose

Marketing OpenClaw AI demonstrates how AI agent architecture, marketing analytics, Python automation, and Jobs-to-be-Done methodology can be combined to support data-driven marketing workflows.

The project also serves as a foundation for adapting AI-assisted marketing processes to new business requirements.

---

**Developed by Tomas Corza**

Growth Marketing & Analytics

[Website](https://tomascorza.me) | [GitHub](https://github.com/Tomas-Corza)