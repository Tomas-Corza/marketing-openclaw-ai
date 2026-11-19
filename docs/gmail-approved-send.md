# Gmail Approved Send

## What is available

This integration provides a **working Python send adapter** with local preview and SHA-256-gated single-email send. It uses the Gmail API but has **no Gmail account connected**, OAuth login interface, refresh-token store, or unattended automations. The existing Gmail customer-inquiry skill continues to create drafts only.

## Connect an email account

1. Create or use an authorized Google Cloud project, enable Gmail API, configure OAuth consent and an OAuth client.
2. Authorize the intended sender mailbox with the least-privilege Gmail send scope: https://www.googleapis.com/auth/gmail.send
3. Obtain a short-lived OAuth access token through your own permitted OAuth login/refresh integration; supply it to the OpenClaw runtime privately as GMAIL_ACCESS_TOKEN. Do not commit token material or put it in prompts.
4. Verify that the authenticated Google mailbox is the intended sender before any live test. This CLI does not verify account identity; implement this in the production connection layer.
5. Test only with a mailbox and recipient you control.

## Preview without connecting

Make a private JSON file (outside the Git repository) named /private/mail.json containing:

    {"to":"recipient@example.com","subject":"Test","body":"Hello from an approved test."}

Run:

    python3 -m tools.gmail_approved_send preview --message /private/mail.json

Review the recipient, entire subject and body and copy the approval_sha256 value. This does not make a network request.

## Send after specific human approval

Set GMAIL_ACCESS_TOKEN in a private runtime environment. Then run:

    python3 -m tools.gmail_approved_send send --message /private/mail.json --approve-sha256 APPROVED_HASH --confirm

The Gmail API returns a message ID on successful send. If the API call fails or times out, check the Gmail Sent folder before retrying because a duplicate may otherwise be sent.

## Limitations

- Gmail-only; not SMTP, Outlook or arbitrary mailboxes.
- One plain-text recipient per message, no HTML, CC/BCC, attachments, Gmail thread replies or bulk mail.
- No built-in consent UI or token refresh; account integration is a separate deployment step.
- No durable send ledger or replay protection. Do not deploy unattended. A production implementation needs audit trails, independent approval checks, verified connected-account identity, rate limits and secure secret storage.
- Mail contents are private and should not be printed to public logs or committed to source control.
- Mailbox owner is responsible for permission, consent, Google policies and applicable anti-spam law.

Official Gmail API docs: https://developers.google.com/workspace/gmail/api/guides/sending
