# Branch inventory and synchronization audit (2026-11-18)

This audit covers the 30 remote branches present when checked against `main` (GitHub compare endpoint). It is a snapshot, not an ongoing guarantee; rerun comparisons after merges.

## What "up to date" means

- **Equal to main:** exactly the same history and tip.
- **Behind only:** safe to fast-forward to main without losing branch-specific commits.
- **Diverged:** contains commits not reachable from main **and** is missing some commits from main. Do **not** force-reset these branches: that would discard distinct history. Review their work before merging main into them, rebasing, or deleting/archive after validating previous PR merges.
- GitHub can show a branch as "ahead" even when equivalent content is already merged via squash/merge commit. Ahead/behind numbers describe *commit ancestry*, not proof of unmerged code.

## Audit findings

- Default `main`: current target, includes finance runner and Streamlit width fix from merged PRs.
- **29 non-main branches examined.** Before the safe update, **28 diverged** and **one was behind only**.
- `feature/shopify-return-processing` was behind-only (0 ahead / 13 behind) and was **fast-forwarded to main**, preserving history.
- The other 28 branches were **not reset or overwritten**; they need per-branch reconciliation before they can accurately be called up to date.

| Branch | Ahead of main | Behind main |
| --- | ---: | ---: |
| docs/ai-attribution-case-study | 2 | 10 |
| docs/feature-attribution-capability | 1 | 9 |
| docs/highlight-commerce-skills | 1 | 19 |
| docs/production-api-architecture-20261118 | 7 | 3 |
| docs/readme-fresh-mac-deployment-details | 1 | 11 |
| docs/streamlit-deployment-maintenance-refresh | 1 | 7 |
| feature/add-return-processing-skill | 1 | 13 |
| feature/ai-shopify-catalog-copy | 6 | 26 |
| feature/customer-inquiry-assistant | 8 | 15 |
| feature/customer-journey-multi-touch-attribution | 29 | 8 |
| feature/ecommerce-operations-dashboard | 16 | 21 |
| feature/finance-automation-demo-20261118 | 7 | 4 |
| feature/fresh-mac-openclaw-deployment | 9 | 12 |
| feature/gmail-inquiry-draft-integration | 6 | 14 |
| feature/merchant-feed-diagnostics | 12 | 23 |
| feature/merchant-product-feed-builder | 9 | 25 |
| feature/shopify-bulk-draft-import | 7 | 17 |
| feature/shopify-bulk-feed-optimization | 9 | 27 |
| feature/shopify-draft-product-creation | 7 | 18 |
| feature/shopify-live-feed-sync | 8 | 24 |
| feature/shopify-product-page-automation | 7 | 28 |
| feature/streamlit-public-demo-deployment | 9 | 20 |
| fix/finance-runner-main-20261118 | 6 | 2 |
| fix/publish-seven-channel-attribution-demo | 7 | 6 |
| fix/streamlit-width-warnings | 1 | 1 |
| maintenance/verify-main-dashboard-docs-tests | 3 | 5 |
| portfolio-neutralization-review-2026-11 | 1 | 4 |
| refactor/modular-shopify-skills | 10 | 22 |
| feature/shopify-return-processing | 0 | 13 **before fast-forward; now equal to main** |

**Note:** Counts were retrieved before writing this documentation and may change after new merges or pushes. `fix/streamlit-width-warnings` can still show diverged because its commit was merged into a different merge commit; this alone is not missing source content.

## Recommended cleanup policy

1. Check each branch's associated PR status and compare **file content**, not just ancestry.
2. For any branch whose feature is already present in `main`, prefer marking it archived/documented or deleting it in a controlled cleanup rather than making unnecessary merge commits. Do not delete branches without confirmation.
3. For truly unmerged work, open a review PR targeting `main` or merge updated `main` into the feature branch after resolving conflicts and running tests.
4. Avoid force pushes and avoid auto-merging every old feature branch: changes may be experimental or obsolete.
5. Recheck with: `git fetch --all --prune` and `git branch -r`; for an individual branch run `git rev-list --left-right --count origin/main...origin/<branch>`. Output is `behind ahead`.
6. For local machine code, use `git switch main && git pull --ff-only origin main` after approved PR merges.

The documentation branch for this audit is itself a new branch and will not be on `main` until the accompanying PR is merged.
