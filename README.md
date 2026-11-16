# Marketing OpenClaw AI

**A customizable AI-powered marketing assistant built on the OpenClaw ecosystem.**

**Developed by Tomas Corza | Growth Marketing & Analytics**

## About This Project

**Marketing OpenClaw AI** is a modular, Python-based marketing automation and analytics framework with **dedicated OpenClaw skills for Shopify e-commerce operations, AI product-content optimization, and Google Merchant Center feed management**, alongside Jobs-to-be-Done (JTBD), email analytics and social engagement analysis.

Its current e-commerce toolkit includes:

- **Shopify product-page automation:** Approval-controlled creation of unpublished Shopify product drafts, including bulk CSV imports with SKUs, prices and variants, plus single-product SEO/content audits and edits through the Shopify Admin GraphQL API.
- **Shopify bulk optimization:** CSV catalog audits, metadata recommendations, and approval-gated batch update manifests.
- **AI product copy generation:** Review-only titles, HTML descriptions, SEO metadata and JTBD messaging hypotheses via the OpenAI Responses API.
- **Product feed builder:** Shopify CSV to Merchant Center-style TSV/RSS feeds, with inventory, pricing and identifier validation.
- **Automated Shopify feed synchronization:** GraphQL catalog extraction, opt-in daily feed generation, and optional GitHub Pages hosting.
- **Merchant Center diagnostics:** Offline feed checks, read-only Merchant API issue analysis, AI remediation suggestions and approval-controlled local feed fixes.
- **Streamlit e-commerce operations dashboard:** Visual catalog health, feed diagnostics, AI recommendations, local approval queues and synthetic demonstration data.
- **AI customer inquiry assistant:** Review-only classification of product questions, order requests, quote inquiries and returns, with approved knowledge grounding, optional opt-in AI drafting and human escalation.
- **Gmail customer inquiry drafts:** Optional authorized Gmail API integration to retrieve one selected customer email, prepare a grounded reply, and create an unsent, human-approved Gmail draft.

**Explore the code:** [OpenClaw skills](skills/) · [E-Commerce Operations Dashboard](dashboard/) · [Synthetic dashboard demo setup](docs/streamlit-community-cloud-deployment.md)

The architecture is adapted from an AI-assisted marketing implementation previously used in practice and is published as a reusable portfolio and development project. **Capabilities differ in readiness:** offline analysis and synthetic demonstrations are available in source; integrations require authorized credentials, configuration and end-to-end testing. No live merchant account, scheduled deployment or hosted Streamlit URL is enabled by simply cloning this repository.

## Capabilities

### OpenClaw Skill Directory

Each e-commerce capability has its own discoverable `skills/<name>/SKILL.md` entry. Skill files describe when and how to run tools; reusable Python implementations remain in `tools/`. Other skills cover JTBD analysis, email analytics and social behavior monitoring.

| Skill | Primary responsibility |
| --- | --- |
| [shopify-product-page-automation](skills/shopify-product-page-automation/SKILL.md) | Create approved unpublished products individually from JSON or in CSV batches with SKUs, prices and variants; audit and update existing product-page content |
| [shopify-bulk-optimization](skills/shopify-bulk-optimization/SKILL.md) | Catalog-wide content audits and reviewed batch updates |
| [shopify-ai-copy-generation](skills/shopify-ai-copy-generation/SKILL.md) | Review-only AI copy drafts and JTBD hypotheses |
| [shopify-product-feed-builder](skills/shopify-product-feed-builder/SKILL.md) | Offline Shopify CSV to Merchant Center TSV/RSS |
| [shopify-feed-sync](skills/shopify-feed-sync/SKILL.md) | Read-only Shopify API feed creation and opt-in scheduling |
| [merchant-feed-diagnostics](skills/merchant-feed-diagnostics/SKILL.md) | Feed diagnostics, Merchant API status review and local fix approval |
| [customer-inquiry-assistant](skills/customer-inquiry-assistant/SKILL.md) | Classify inquiries and draft factual, unapproved, unsent customer responses from approved product/policy facts |
| [gmail-customer-inquiry-drafts](skills/gmail-customer-inquiry-drafts/SKILL.md) | Read one explicitly selected authorized Gmail message and create an unsent reply draft only after human approval |

Skills do not automatically activate credentials, scheduled jobs, model API access or live store writes. Set up and test each integration separately.

**Additional marketing skills:** [JTBD Analysis](skills/jtbd-analysis/SKILL.md) · [Email Analytics](skills/email-analytics/SKILL.md) · [Social Behavior Monitor](skills/social-behavior-monitor/SKILL.md).

**Featured application:** [AI E-Commerce Operations Dashboard](dashboard/README.md) — the public demonstration entrypoint is `dashboard/public_app.py`, using synthetic data without uploads or live API connections.

### AI E-Commerce Operations Dashboard (Streamlit)

A local-first Streamlit control center combining existing Shopify catalog analysis, Google Merchant product-feed diagnostics, synthetic demonstrations, previously generated AI content drafts, approval-controlled **local** feed corrections, and session-only activity history.

- Five views: Overview, Product Optimization, Merchant Feed Health, Approval Queue, Activity.
- Reuses existing `tools.shopify_bulk_feed` and `tools.merchant_feed_diagnostics` functions rather than duplicating calculation rules.
- Read-only imports for merchant catalog and AI reports; hash-verified, human-approved downloadable feed changes.
- Synthetic fixtures allow a portfolio demo without credentials or external API calls.
- No automatic Shopify writes, live Merchant Center changes, job execution or hosted deployment.

**Included:** `dashboard/app.py`, `dashboard/logic.py`, `dashboard/requirements.txt`, `dashboard/README.md`, synthetic examples and offline tests.

```bash
python -m pip install -r dashboard/requirements.txt
streamlit run dashboard/app.py
```

See [Dashboard setup and safety](dashboard/README.md) and [Streamlit Community Cloud public demo deployment](docs/streamlit-community-cloud-deployment.md). The public demo entrypoint is `dashboard/public_app.py` (synthetic-only; no uploads); deployment requires the owner's Streamlit account.

### AI Customer Inquiry Assistant (review-only)

Prepare grounded customer-service reply drafts for product questions, order status, B2B quote requests, returns and general inquiries. Uses approved local product and policy knowledge, classifies the message and flags certain sensitive topics for employee review. Optional OpenAI Responses API drafting is **opt-in** and requires authorization to share inquiry data externally.

- Offline template mode requires no API keys or internet connection.
- Outputs proposed reply, evidence IDs, missing information, category and review/escalation flags.
- Always records `approved: false` and `sent: false`; **no automatic email, SMS, Shopify lookup, CRM connection, or customer messaging** is implemented.
- Customer data and private drafts must not be committed to the public repository.

**Included:** [Skill instructions](skills/customer-inquiry-assistant/SKILL.md), [Python implementation](tools/customer_inquiry_assistant.py), [setup guide](docs/customer-inquiry-assistant.md), fictional fixtures and mocked offline tests.

```bash
python3 -m tools.customer_inquiry_assistant --inquiry examples/customer_inquiry_sample.json --knowledge examples/customer_inquiry_knowledge_sample.json --output /tmp/customer-inquiry-draft.json
```

See [Customer Inquiry Assistant setup](docs/customer-inquiry-assistant.md). Real inbox/Shopify integrations and sending workflows require separate authorization, development, security review and testing.

### Gmail Customer Inquiry Draft Integration (API-ready)

Extend the [AI Customer Inquiry Assistant](skills/customer-inquiry-assistant/SKILL.md) to process **one authorized Gmail message at a time** and prepare a reply inside the original email thread. The connector classifies the selected question, uses a separately approved product/policy knowledge JSON and generates a review-only reply. A matching SHA-256 fingerprint and explicit confirmation are required before creating a **Gmail draft**.

- Uses Gmail API `users.messages.get` for a selected message and `users.drafts.create` for approved replies. **Never sends email.**
- Supports offline template replies or optional OpenAI drafting only with permission to share the inquiry externally.
- Excludes certain automated/list emails, spam and sensitive inquiries.
- Requires a merchant-authorized OAuth token with suitable Gmail read and compose scopes; no credentials or live mailbox are provided by the repository.
- No inbox monitoring, auto-sending, live order lookup, recurring polling or multi-message processing. Production use requires privacy review and authorized end-to-end testing.

**Included:** [OpenClaw skill](skills/gmail-customer-inquiry-drafts/SKILL.md), [Python Gmail connector](tools/gmail_inquiry_drafts.py), [setup guide](docs/gmail-customer-inquiry-drafts.md), and mocked tests.

```bash
# With authorized GMAIL_ACCESS_TOKEN configured privately:
python3 -m tools.gmail_inquiry_drafts preview --message-id GMAIL_MESSAGE_ID --knowledge /private/approved-knowledge.json

# Only after human approval of the exact recipient and reply:
python3 -m tools.gmail_inquiry_drafts create --message-id GMAIL_MESSAGE_ID --knowledge /private/approved-knowledge.json --approve-sha256 APPROVED_PREVIEW_HASH --confirm
```

See [Gmail inquiry draft guide](docs/gmail-customer-inquiry-drafts.md) for configuration, privacy limitations and safeguards.

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

### Shopify Product Page Automation & Draft Creation (API-ready)

Create new unpublished Shopify product drafts individually from verified JSON or in reviewed CSV batches with SKUs, prices and variants. The skill also audits existing product pages, previews proposed changes, and applies explicitly approved title, HTML description and SEO metadata updates.

- New product draft creation: validate merchant-verified title, HTML description, vendor, type, SEO metadata, tags and HTTPS image URLs; approve exact preview before writing a Shopify DRAFT.
- Bulk CSV creation: group variant rows by product, validate SKUs/prices/options, require fingerprint-matched merchant review, create DRAFT products in bounded batches and write a private per-product journal.
- Offline audit with synthetic product JSON.
- Authorized Shopify read and write integration with environment-provided credentials.
- Read-before-write preview; explicit confirmation required to update.
- OpenClaw skill instructions for fact-checked, JTBD-informed content proposals.
- No live Shopify credentials, autonomous text generation, or scheduled publishing included.

**Included:** `tools/shopify_product_pages.py`, `tools/shopify_product_create.py`, `tools/shopify_bulk_product_create.py`, `skills/shopify-product-page-automation/SKILL.md`, setup guides, mocked offline tests and synthetic examples.

#### Preview Shopify product creation (no credentials required)

**Single product from JSON:**

```bash
python3 -m tools.shopify_product_create preview --input examples/shopify_new_product_sample.json
```

**Multiple products and variants from CSV:**

```bash
python3 -m tools.shopify_bulk_product_create preview --input examples/shopify_bulk_product_create_sample.csv
```

The bulk CSV accepts product handles, names, descriptions, SEO fields, SKUs, prices, tags and up to three named variant options (such as size, finish or color). Rows sharing a handle are grouped into one product. A preview validates the file and displays a SHA-256 fingerprint identifying the exact data being reviewed.

#### Create drafts with merchant approval

After configuring an authorized Shopify app and obtaining explicit merchant approval for the exact content and target store:

```bash
# One approved unpublished draft:
python3 -m tools.shopify_product_create create --input /private/new-product.json --approve-sha256 APPROVED_PREVIEW_SHA --confirm

# A reviewed CSV batch (defaults to at most 10 products per run):
python3 -m tools.shopify_bulk_product_create create --input /private/catalog.csv --approve-sha256 APPROVED_PREVIEW_SHA --confirm --journal /private/new-import-log.jsonl --max-products 10
```

- Both workflows create **DRAFT** products and do not publish them.
- Bulk imports check existing product handles and stop rather than updating an existing product; they record attempted and successful creations in a private journal.
- Bulk SKU uniqueness is checked **within the CSV**, not against all existing store SKUs. Bulk import batches are limited to 25 products per approved run.
- The single-product JSON workflow supports image URLs, but the bulk CSV workflow **does not** import images.
- The bulk importer does not set inventory quantities, tax/shipping settings, or publish products. Review those separately in Shopify.
- Shopify API permissions, authorized credentials and end-to-end tests with a development store are required before production use. Offline mocked tests alone do not verify live-store behavior.

**Existing product content audit:**

```bash
python3 tools/shopify_product_pages.py audit --input examples/shopify_product_sample.json
```

See [single-product setup](docs/shopify-product-page-automation.md), [bulk CSV creation guide](docs/shopify-bulk-product-create.md), and [Skill #1 instructions](skills/shopify-product-page-automation/SKILL.md) for complete steps, permissions and safeguards.

### Shopify Bulk Feed Optimization (API-ready)

Extend the Shopify product-page skill across a product catalog with a Shopify CSV export.

- Group Shopify variant rows into unique products.
- Audit titles, descriptions and custom SEO fields at catalog scale.
- Export machine-readable JSON findings and conservative metadata drafts.
- Prepare product-ID-mapped, approval-required API update manifests.
- Apply capped batches with stale-content checks and private JSONL audit logs.
- No AI-written copy or unattended product publishing by default.

**Included:** `skills/shopify-bulk-optimization/SKILL.md`, `tools/shopify_bulk_feed.py`, `docs/shopify-bulk-feed-optimization.md`, `tests/test_shopify_bulk_feed.py`, and `examples/shopify_bulk_feed_sample.csv`.

```bash
python3 tools/shopify_bulk_feed.py analyze --input examples/shopify_bulk_feed_sample.csv --output /tmp/shopify-audit.json
```

See [Bulk Shopify feed guide](docs/shopify-bulk-feed-optimization.md).

### AI-Powered Shopify Catalog Copy Generation (review-only)

Generate proposed product-page titles, descriptions and SEO metadata at catalog scale using the OpenAI Responses API and verified merchant source fields. The agent produces a Jobs-to-be-Done messaging hypothesis and review notes for each product. API access and merchant authorization are required; these are **drafts only**, not autonomous publishing.

- Strict JSON output, escaped HTML, per-product errors and rate/cost caps.
- No live Shopify writes: human review and explicit approvals remain mandatory.
- Generated claims require independent verification against product facts.

**Included:** `skills/shopify-ai-copy-generation/SKILL.md`, `tools/shopify_ai_copy.py`, `tests/test_shopify_ai_copy.py`, `docs/shopify-ai-copy-generation.md`.

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

**Included:** `skills/shopify-product-feed-builder/SKILL.md`, `tools/shopify_feed_builder.py`, `docs/shopify-product-feed-builder.md`, `examples/shopify_merchant_feed_sample.csv`, and offline tests.

```bash
python3 tools/shopify_feed_builder.py --input examples/shopify_merchant_feed_sample.csv --store-url https://example.com --output /tmp/merchant-feed.tsv --rejects /tmp/merchant-feed-errors.json
```

See [Feed creation guide](docs/shopify-product-feed-builder.md).

### Scheduled Shopify API Feed Sync (opt-in)

Generate Google Merchant Center-style RSS/TSV feeds directly from Shopify GraphQL product and variant data, without manual CSV exports. A GitHub Actions workflow can regenerate the feed daily and optionally deploy approved public catalog information to GitHub Pages.

- Shopify Admin GraphQL cursor pagination and variant-aware catalog extraction.
- Validation of publication status, identifiers, prices, inventory, product assets, and feed fields.
- Strict rejection of invalid feed entries by default; private error reports.
- Repository secrets for store credentials; **scheduled sync and public Pages publishing remain disabled until explicitly enabled**.
- No Shopify product edits or automatic Google Merchant Center submissions.

**Included:** `skills/shopify-feed-sync/SKILL.md`, `tools/shopify_live_feed_sync.py`, `docs/shopify-live-feed-sync.md`, `.github/workflows/shopify-live-feed.yml`, and offline unit tests.

See [Live Shopify feed setup](docs/shopify-live-feed-sync.md).

### AI Product Feed Diagnostics & Optimization Agent (API-ready)

Inspect Merchant Center-style TSV/RSS catalog feeds, compare offline issues with authorized Google Merchant API processed-product issues, and prioritize corrections.

- Offline validation for required feed attributes, GTIN checksums, IDs, prices, availability and URLs.
- Read-only Google Merchant API v1 `accounts.products.list` adapter for item issues and disapproval statuses.
- Optional AI-based issue explanations and prioritized remediation tasks (OpenAI Responses API).
- Explicitly approved, SHA-256 snapshot-checked **local-only** correction exports; no Shopify or Merchant API writes.
- Synthetic test fixtures, mocked tests and GitHub Actions CI.

**Included:** `tools/merchant_feed_diagnostics.py`, `tools/merchant_api_connector.py`, `tools/merchant_feed_ai_triage.py`, `skills/merchant-feed-diagnostics/SKILL.md`, `docs/merchant-feed-diagnostics.md`.

```bash
python3 tools/merchant_feed_diagnostics.py audit --feed /private/merchant-feed.tsv --output /private/merchant-diagnostics.json
```

See [Merchant feed diagnostics guide](docs/merchant-feed-diagnostics.md). No account connection is active by default.

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