# Gmail Customer Inquiry Draft Integration

The review-first Gmail integration for Marketing OpenClaw AI's customer-inquiry-assistant.

## What it does

With an authorized Gmail OAuth token, reads **one explicitly specified email**, classifies it using existing offline customer inquiry tools, and prepares a grounded reply with approved product/policy facts. Preview is read-only. After human review of the exact reply and its SHA-256 fingerprint, the connector creates a **Gmail Draft** within the original thread.

**No email is ever sent automatically.** There is no inbox polling, live Shopify customer/order access, automatic approval or mass-drafting.

## Authorization and Gmail API scopes

Use a merchant-approved Google Cloud OAuth application and the Gmail API. An approved OAuth token must permit reading the selected message and creating a draft; for example, `gmail.readonly` plus `gmail.compose` scopes as authorized by Google. A Gmail token can expire; refresh via your own authorized OAuth client rather than storing refresh tokens here. This repository intentionally contains no OAuth consent server, token refresh flow or client credentials.

Use private environment variables (never commit real credentials):

```bash
export GMAIL_ACCESS_TOKEN="AUTHORIZED_OAUTH_ACCESS_TOKEN"
```

For the optional AI mode, also configure a private `OPENAI_API_KEY`, `--ai` and `--allow-external-data` only when the mailbox owner has explicitly authorized sending inquiry information to the AI provider.

## Preview one message

```bash
python3 -m tools.gmail_inquiry_drafts preview \
  --message-id GMAIL_MESSAGE_ID \
  --knowledge /private/approved-knowledge.json
```

Review the returned recipient, subject, full reply body, missing details, evidence IDs and `approval_sha256`. Never copy real customer messages or response previews into public GitHub issues.

## Create an unsent draft after human approval

```bash
python3 -m tools.gmail_inquiry_drafts create \
  --message-id GMAIL_MESSAGE_ID \
  --knowledge /private/approved-knowledge.json \
  --approve-sha256 EXACT_HASH_FROM_PREVIEW \
  --confirm
```

The connector re-reads the source message and recreates the proposal. A matching hash is required; if the source message or proposal changes, stop and preview again. The connector uses Gmail `users.drafts.create` with `threadId`, `In-Reply-To` and `References` headers. It never calls `messages.send` or `drafts.send`.

**Important:** If Gmail responds with a timeout, a draft might exist even when its ID is not returned. Inspect Gmail Drafts and the relevant thread before attempting another creation. No automatic deduplication is claimed.

## Limitations and privacy

- The connector requires an actual authorized Gmail OAuth token; none is provisioned by the repository.
- It works only with plain-text email messages and single explicitly selected message IDs.
- Product facts come from separately reviewed local JSON, **not** a live Shopify connection.
- It will not access order status, pricing or customer history.
- Some sensitive and auto-generated inquiries are blocked; this is not a complete safety or policy compliance system.
- Draft creation is an external write to Gmail, so the CLI confirmation is not itself business authorization.
- Store customer information under private access controls and follow organizational retention rules. API responses and AI drafts should be reviewed for privacy and accuracy.
- Google OAuth scopes and Gmail API availability depend on the application configuration and authorization requirements; test end-to-end only with a permitted development or test mailbox.

## Offline tests

```bash
python3 -m unittest discover -s tests -p 'test_gmail_inquiry_drafts.py' -v
```

Tests use mocked Gmail requests, with no access to real messages.

Gmail API documentation:
- https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/get
- https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.drafts/create
- https://developers.google.com/workspace/gmail/api/guides/sending
