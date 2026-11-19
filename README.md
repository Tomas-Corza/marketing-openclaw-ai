# Marketing OpenClaw AI

**AI agents for marketing, e-commerce, finance, and business operations.**

Marketing OpenClaw AI is a modular Python-based framework **built for OpenClaw AI agents**. It combines reusable agent skills, analytics tools, and approval-controlled workflows to help businesses reduce repetitive tasks, identify actionable insights, and improve operational consistency.

**Created by Tomas Corza** · [Portfolio](https://tomascorza.me) · [Other GitHub projects](https://github.com/Tomas-Corza)

> **Explore the work:** This is a portfolio and development repository with working offline tools, example workflows, and synthetic demonstrations. 

## The business value

Businesses often lose time moving data across systems, auditing product catalogs, reconciling reports, preparing responses, and reviewing exceptions. Marketing OpenClaw AI demonstrates how these workflows can become more repeatable and inspectable while retaining human oversight.

- **Reduce manual work** in reporting, merchandising, customer operations, and financial reviews.
- **Improve visibility** with consistent data validation, dashboards, and exception reporting.
- **Support better decisions** with marketing analytics, attribution models, and Jobs-to-be-Done analysis.
- **Protect important workflows** through explicit approval requirements before consequential actions.
- **Adapt to different organizations** using modular OpenClaw skills and Python automation tools.

## Business applications

| Area | Example capabilities | Potential business benefit |
| --- | --- | --- |
| **E-commerce** | Shopify product drafts, catalog optimization, feed generation and diagnostics | More efficient merchandising and fewer preventable catalog issues |
| **Marketing analytics** | Email and social analysis, observed-journey attribution, JTBD messaging analysis | Faster reporting and more informed optimization |
| **Customer operations** | Inquiry classification, customer-reply drafts, return-policy reviews | More consistent handoffs and less repetitive triage |
| **Finance and accounting** | AR/AP reviews, invoice matching, reconciliation checks, payroll/time review, exception monitoring | Streamlined reviews and clearer visibility into discrepancies |

The listed capabilities do not imply that live third-party accounts are connected. Available functionality and integration requirements are described below.

## Featured: Finance Automation Control Center

The [Finance Automation Control Center](finance/dashboard.py) explores how OpenClaw-based workflows can support accounting teams through a unified operational view. Its synthetic prototype includes:

- Accounts receivable and payable review
- Invoice and purchase-order verification
- Bank and ledger reconciliation checks
- CRM job references and time/payroll review
- Shift-level timekeeping checks (clock-in/out, breaks, overlapping entries, duplicate IDs, approval checks) with an exception-gated CSV of reviewed hours
- Exception routing, audit records, and reporting
- A scheduled Python runner for deterministic checks

This demonstration processes **fictional financial records**. It does not connect to live QuickBooks, banks, payroll, or CRM accounts, execute model-driven financial agents, or perform production financial writes. These would require separately authorized implementation and testing.

**Explore:** [Dashboard code](finance/dashboard.py) · [OpenClaw finance skill](skills/finance-operations/SKILL.md) · [Finance demonstration overview](docs/finance-automation-demo.md) · [Production integration architecture](docs/production-integration-architecture.md)

## Featured: AI E-Commerce Operations Dashboard

The [Streamlit operations dashboard](dashboard/README.md) makes automation workflows easier to explore through views for product optimization, catalog health, Merchant Center feed diagnostics, AI content recommendations, and marketing attribution examples.

The public showcase uses **synthetic data only**; it does not upload customer files or access live stores, advertising accounts, or the agent's command-line tools.

**Explore:** [Dashboard source](dashboard/) · [Public demonstration entry point](dashboard/public_app.py) · [Deployment guide](docs/streamlit-community-cloud-deployment.md)

## Featured: Marketing analytics and attribution

The repository includes tools for **observed, identity-linked customer journeys**, with first-touch, last-touch, linear, position-based, and time-decay models. A Shopify + GA4 pipeline can match suitably collected GA4 event exports to Shopify orders when consent, identifiers, and timestamps permit.

The dashboard also illustrates seven **fictional** acquisition channels: Meta Ads, Google Ads, Microsoft Ads, Etsy referral, Amazon referral, ChatGPT referral, and Google organic. These are examples, **not seven live platform integrations**. Aggregate ad reports cannot by themselves establish customer-level multi-touch journeys, and attribution is not proof of incrementality.

**Explore:** [Attribution engine](tools/multi_touch_attribution.py) · [Shopify + GA4 pipeline guide](docs/shopify-ga4-bigquery-pipeline.md) · [Attribution limitations](docs/multi-touch-attribution.md)

**Related case study:** [AI Marketing Analytics and Attribution](docs/ai-marketing-attribution-case-study.md) describes a cross-channel reporting implementation and its business application. The complete four-platform case-study integration is not published as runnable code in this repository.

## Built for OpenClaw AI agents

Each reusable skill defines a business task and its operating boundaries. Python tools perform structured analysis and processing; authorized integrations and human checkpoints can be added where appropriate.

| OpenClaw skill | Application |
| --- | --- |
| [Shopify product-page automation](skills/shopify-product-page-automation/SKILL.md) | Review and create unpublished product drafts; audit content |
| [Shopify bulk optimization](skills/shopify-bulk-optimization/SKILL.md) | Identify catalog-wide improvements and prepare reviewed updates |
| [AI product copy generation](skills/shopify-ai-copy-generation/SKILL.md) | Generate review-only product descriptions and SEO drafts |
| [Product feed builder](skills/shopify-product-feed-builder/SKILL.md) | Convert Shopify CSV exports into validated feed formats |
| [Shopify feed synchronization](skills/shopify-feed-sync/SKILL.md) | Optional authorized catalog extraction and feed generation |
| [Merchant feed diagnostics](skills/merchant-feed-diagnostics/SKILL.md) | Detect feed issues and recommend local corrections |
| [Customer inquiry assistant](skills/customer-inquiry-assistant/SKILL.md) | Classify questions and prepare factual draft responses |
| [Gmail inquiry drafts](skills/gmail-customer-inquiry-drafts/SKILL.md) | Prepare unsent replies to selected authorized messages |
| [Gmail approved sending](skills/gmail-approved-send/SKILL.md) | Preview and send one exact human-approved email with separately authorized Gmail OAuth |
| [Shopify return processing](skills/shopify-return-processing/SKILL.md) | Screen verified requests and prepare proposals for review |
| [JTBD analysis](skills/jtbd-analysis/SKILL.md) | Analyze messaging against customer motivations |
| [Email analytics](skills/email-analytics/SKILL.md) | Summarize campaign engagement, orders, and revenue |
| [Social behavior monitor](skills/social-behavior-monitor/SKILL.md) | Analyze structured engagement data |
| [Finance operations](skills/finance-operations/SKILL.md) | Demonstrate accounting checks, reviews, and exception workflows |
| [Timekeeping review](skills/timekeeping-review/SKILL.md) | Review fictional shift records, flag invalid or overlapping time, and prepare approved-hours CSV exports |

## Try the project

### Install the OpenClaw skills on macOS

Requirements: **macOS, Git, Python 3.10+**, and permission to install software. Review the installation script and the [official OpenClaw getting-started guide](https://docs.openclaw.ai/start/getting-started) first.

```bash
git clone https://github.com/Tomas-Corza/marketing-openclaw-ai.git
cd marketing-openclaw-ai
bash install.sh
```

The script checks the environment, requests confirmation before downloading the official OpenClaw installer when needed, and copies project skills and shared tools into the workspace without silently overwriting conflicting files.

Already using OpenClaw?

```bash
bash install.sh --skip-openclaw
```

You still need to complete OpenClaw onboarding and configure any optional services separately. [Installation and troubleshooting guide](docs/fresh-mac-install.md).

### Explore the synthetic dashboards

```bash
python3 -m pip install -r dashboard/requirements.txt

# E-commerce dashboard
streamlit run dashboard/public_app.py

# Finance prototype (run separately)
streamlit run finance/dashboard.py
```

### Run a scheduled-style finance check

```bash
python3 -m finance.automation_runner --source synthetic --output-dir ./var/finance
```

These examples are for evaluation, not production financial processing. See the [finance setup guide](docs/local-finance-prototype-guide.md) and [runner deployment guide](docs/finance-scheduling-setup.md).

## Implementation approach

A real business deployment starts by identifying repetitive tasks and selecting appropriate automation boundaries. From there, the process involves integrating only authorized systems, normalizing data, adding validation and exceptions, testing with representative records, and documenting human review and escalation points.

**Available in this repository:** Offline Python analysis and validation, reusable skill definitions, dashboards, synthetic example data, approval-gated workflow components, and selected optional API-capable tools.

**Requires separate configuration or development:** Live third-party integrations, credentials and permissions, financial-system adapters, operational schedules, secure production deployment, and end-to-end validation. Installing this repository does not automatically send customer messages, issue refunds, publish products, or change accounting records. The [Gmail approved-send adapter](docs/gmail-approved-send.md) can send a single approved plain-text email **only after separate Gmail OAuth configuration and explicit per-message approval**; the existing customer inquiry workflow remains draft-only.

## Repository guide

| Location | Contents |
| --- | --- |
| [`skills/`](skills/) | Reusable OpenClaw skill instructions |
| [`tools/`](tools/) | Python analytics and automation tools |
| [`finance/`](finance/) | Finance automation prototype |
| [`dashboard/`](dashboard/) | E-commerce dashboard |
| [`examples/`](examples/) | Fictional sample inputs |
| [`docs/`](docs/) | Setup, architecture, and integration guides |
| [`tests/`](tests/) | Validation and offline tests |
| [`install.sh`](install.sh) | macOS installer |

Agent configuration files such as `IDENTITY.md`, `SOUL.md`, `AGENTS.md`, and `TOOLS.md` describe identity, behavior, and tool usage conventions.

## About the creator

**Tomas Corza** is an e-commerce, AI automation, and growth marketing specialist who combines Shopify operations, Python, SQL, marketing analytics, and practical AI implementation. Marketing OpenClaw AI demonstrates how business workflows can be translated into modular agent capabilities backed by structured tools.

**[Portfolio and case studies](https://tomascorza.me)** · **[GitHub](https://github.com/Tomas-Corza)**

---

*This public project uses synthetic examples and does not publish live merchant credentials, private customer records, or confidential business datasets. Third-party access and production deployment require appropriate permissions, security review, and testing. Code reuse should respect applicable ownership and licensing obligations.*
