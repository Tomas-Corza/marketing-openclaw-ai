# AI Customer Inquiry Assistant

A review-first, privacy-conscious prototype that classifies an authorized customer question and prepares a grounded customer support reply using approved product and policy data. Useful for a Shopify or B2B e-commerce business.

## Current features

- Classifies questions into product information, order status, quote request, returns, or general.
- Selects product evidence **only when the approved product ID or name appears in the inquiry** and attaches category-relevant approved policies.
- Creates a plain-text, factual template response without network access by default.
- Optionally generates an AI-assisted reply through the OpenAI Responses API after explicit opt-in, with a structured schema and `store: false`.
- Flags a small set of safety/legal/escalation phrases for employee review.
- Writes JSON containing category, evidence IDs, draft text, missing information, approval status and an SHA-256 fingerprint.
- Drafts are always `approved: false`, `sent: false`, `approval_status: pending`.
- Private output files are created with owner-only access and cannot silently overwrite an existing file.

## Demonstration (offline, no credentials)

From the repository root:

```bash
python3 -m tools.customer_inquiry_assistant \
  --inquiry examples/customer_inquiry_sample.json \
  --knowledge examples/customer_inquiry_knowledge_sample.json \
  --output /tmp/customer-inquiry-draft.json
```

The sample uses fictional products and has no real customer information. Use a new output path for each run.

## Input format

Inquiry file:

```json
{"id":"case-001","subject":"Example Pendant specifications","message":"What voltage does the Example Pendant use?"}
```

Knowledge file:

```json
{
  "products": [
    {
      "id":"fixture-001",
      "name":"Example Pendant",
      "facts":{"Voltage":"120V"},
      "url":"https://example.com/products/example-pendant"
    }
  ],
  "policies":[
    {"id":"returns","category":"returns","text":"Our team reviews returns case by case."}
  ]
}
```

Only add product facts or policy text that an authorized employee has checked. Real customer messages and knowledge should remain in appropriately protected private files, not this public repository.

## Optional AI generation

Set `OPENAI_API_KEY` privately; optionally set `OPENAI_MODEL`. Use only if the merchant authorizes sending the specific inquiry and selected evidence to the AI provider:

```bash
python3 -m tools.customer_inquiry_assistant \
  --inquiry /private/inquiry.json \
  --knowledge /private/approved-knowledge.json \
  --output /private/inquiry-draft.json \
  --ai --allow-external-data
```

AI drafting can incur API costs. Model responses are not guaranteed to be factual or policy-compliant. A human must verify the output before communicating with the customer. Never place live credentials or customer data in Git.

## Limitations

This is **not** an inbox integration or a real-time chatbot. It does not retrieve real Shopify products, order details, shipping status or actual quote prices. It does not send emails or messages or update a CRM. Keyword-based category detection can misclassify inquiries; product matching currently relies on exact name/ID references. Escalation terms are only a partial screening mechanism. Template mode may include approved information that's not relevant to every part of a question, so the draft must be reviewed. AI mode sends provided inquiry content and selected evidence to an external provider only with explicit opt-in.

## Tests

```bash
python3 -m unittest discover -s tests -p 'test_customer_inquiry_assistant.py' -v
```

The tests use fictional data and mocked AI responses; they do not represent an end-to-end integration with a live Shopify store or email system.
