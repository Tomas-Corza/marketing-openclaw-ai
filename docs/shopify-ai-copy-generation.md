# AI-powered Shopify product feed optimization

Generate **review-only** AI product-page descriptions and SEO metadata from an authorized Shopify CSV catalog using OpenAI's Responses API.

## Setup

- Python 3.10+; standard library only.
- Obtain an OpenAI API key and access to a Structured Outputs-compatible model. ChatGPT subscription credentials are not API credentials.
- Use authorized Shopify CSV with Handle, Title and Body (HTML), optionally Vendor and Type.
- Set OPENAI_API_KEY and optionally OPENAI_MODEL in your private environment. Never commit keys, merchant exports, or reports.
- Confirm the merchant authorizes sending catalog information to the AI provider. API usage may incur charges.

## Generate a report

```bash
export OPENAI_API_KEY='YOUR_KEY_IN_LOCAL_SECRET_STORAGE'
python3 tools/shopify_ai_copy.py --input examples/shopify_bulk_feed_sample.csv --output /tmp/shopify-ai-review.json --max-products 10 --delay 1
```

Each item contains generated title, escaped HTML description, SEO title and SEO description, a JTBD angle *hypothesis*, and review notes. Source product facts are sent to the model. The output always marks approved=false and publishable=false. **No Shopify write occurs.**

Model prompts forbid unverified claims, but generation may still hallucinate. Verify product facts, claims and language against authoritative merchant specifications before using.

## Approved publishing path

1. Independently confirm the correct Shopify Product IDs; CSV handles are not IDs.
2. Use the existing bulk tool's `prepare` command on those verified IDs to obtain current product content hashes and private manifests.
3. Manually copy only authorized, fact-checked suggestions into the matching product's `changes` entry. Preserve ID and snapshot hash.
4. Remove unapproved entries, mark individually authorized entries approved=true, then use the existing bulk tool's `apply --confirm` flow only with merchant authorization.
5. Re-fetch products to verify and retain a private audit log.

The AI report cannot be used as a write manifest directly. There is no autonomous publishing or unattended scheduling.

## Limitations

- Default maximum 10 products and configurable maximum 100 per run for API-cost control.
- Retries on temporary 429/5xx responses only; errors are reported per product.
- This does not optimize Google Merchant Center feeds or automatically map handles to product IDs.
- Keep generated catalogs and reports private and outside public source control.

## Test

```bash
python3 -m unittest tests.test_shopify_ai_copy
```

References: https://platform.openai.com/docs/api-reference/responses and https://platform.openai.com/docs/guides/structured-outputs