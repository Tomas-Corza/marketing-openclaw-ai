---
name: shopify-ai-copy-generation
description: Generate review-only AI proposals for Shopify product titles, descriptions, SEO metadata, and JTBD hypotheses from authorized Shopify product CSV exports.
---

# Shopify AI Copy Generation

Use this skill when a merchant requests AI-assisted product copy across a Shopify catalog. This skill creates **drafts only**, not store changes or approved feed manifests.

## Tools and setup
- `tools/shopify_ai_copy.py`
- `docs/shopify-ai-copy-generation.md`
- Synthetic sample input: `examples/shopify_bulk_feed_sample.csv`
- Python 3.10+ and a compatible OpenAI Responses API model.
- An authorized, locally managed `OPENAI_API_KEY`; `OPENAI_MODEL` is optional.

## Workflow
1. Verify merchant permission to submit product descriptions and related attributes to the external AI provider. Do not upload sensitive or proprietary data without consent.
2. From the repository root, run:
   `python3 tools/shopify_ai_copy.py --input examples/shopify_bulk_feed_sample.csv --output /private/ai-drafts.json --max-products 10`.
3. Review the resulting JSON proposals for product titles, escaped HTML descriptions, SEO titles/descriptions, Jobs-to-be-Done messaging **hypotheses**, and verification notes.
4. Independently verify every assertion, specification, brand claim, marketing promise and HTML field against authoritative merchant records. Generated copy can be wrong.
5. For individually approved live changes, follow the *separate* `shopify-bulk-optimization` skill to prepare a Shopify Product ID-mapped, current-snapshot manifest. Manually transfer only approved changes and confirm again before applying.

## Guardrails
- Do not mistake model output for verified product facts or demonstrated SEO/conversion uplift.
- The draft file contains `approved: false` and `publishable: false`; it is **not a publishing manifest**.
- The model/API call can incur costs. Keep requests bounded; never disclose credentials in prompts or Git.
- No direct Shopify writes, autonomous approval or scheduled execution are provided by this script.

Related skills: `shopify-bulk-optimization`, `shopify-product-page-automation`.
