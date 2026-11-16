# Shopify Return Processing — Offline Prototype

This skill prepares **return-case reviews and draft communications**, rather than actually issuing returns or refunds.

## What it does

- Validates merchant-supplied Shopify order and fulfillment line-item identifiers, dates and quantities.
- Evaluates a request against a simple approved return policy (window, excluded tags, unopened condition).
- Flags missing information and policy exceptions for human review.
- Produces a proposed return manifest, a customer reply draft and a review SHA-256 fingerprint.
- Writes a private JSON proposal (0600) without overwriting an existing output file.

**What it does not do:** Access Shopify, verify live order details, create an official Shopify return, generate an RMA number or label, issue/refuse refunds, update inventory, send email or make binding eligibility/legal decisions.

## Quick start

From the repository root (Python 3.10+):

    python3 tools/shopify_return_processing.py --case examples/return_case_sample.json --policy examples/return_policy_sample.json --output /tmp/return-review-example.json

Use a **new output filename** for every run. Inspect the JSON draft. Keep real cases and policies in private, access-controlled directories outside your public repository.

## Test

    python3 -m unittest discover -s tests -p 'test_shopify_return_processing.py' -v

The demo uses fictional fixture and order data. The tests are offline. Before introducing a real-store integration, validate Shopify's supported return mutation and fields for your API version, implement OAuth/token scope controls and idempotency protections, and test against an authorized development store. Keep refund, restock and outbound-email actions separate, logged and explicitly approved.
