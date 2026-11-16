# Fresh Mac mini deployment

This kit installs official OpenClaw (after an explicit confirmation) and copies all repository skill folders and supporting Python source into the active OpenClaw workspace. It does not automatically configure model credentials, business APIs, or production security.

Official references:
- https://docs.openclaw.ai/start/getting-started
- https://docs.openclaw.ai/tools/skills

## Start on a new Mac

Prerequisites: Git, Python 3.10+, internet access, and permission to install OpenClaw. On macOS, install Apple's Command Line Tools if Git is missing. Use a dedicated user account and review code and permissions before running agent tools.

Run from Terminal:

    git clone https://github.com/Tomas-Corza/marketing-openclaw-ai.git
    cd marketing-openclaw-ai
    bash install.sh

The script checks for filename conflicts before performing installation. If the OpenClaw CLI is missing, it shows the official installer URL and asks before downloading and running the official installer. Follow interactive model-provider onboarding and Gateway setup. If OpenClaw is already installed separately (including the native macOS application), run:

    bash install.sh --skip-openclaw

The script copies the repository's 12 skill folders (nine e-commerce/customer-operation skills plus email analytics, JTBD analysis, and social behavior monitoring) along with tools, docs, and examples into the default workspace at ~/.openclaw/workspace. It never intentionally overwrites different existing files; if conflicts exist it stops before copying and asks you to resolve them yourself. Run it again if all existing files are identical. It does not replace AGENTS.md, SOUL.md, USER.md, OpenClaw configuration, sessions, or memories.

Custom workspaces may be specified with --workspace=/absolute/path; this must match your OpenClaw agent's configured workspace.

## Verify

    python3 verify_installation.py

Confirm that the OpenClaw CLI can run, the Gateway is configured and running, and the newly installed skills appear in your agent's workspace. The included verifier checks installed skill definitions and representative Python tools; it does not certify actual model authentication, tool orchestration, or business API connections.

Run offline tests from the cloned repository:

    python3 -m unittest discover -s tests -p 'test_fresh_install.py' -v

Shared skill tools generally assume execution from the workspace root (for example, cd ~/.openclaw/workspace && python3 -m tools.customer_inquiry_assistant ...). They are not installed as independent system-wide packages. The core Python tools use the standard library; optional Streamlit dashboard dependencies are separate under dashboard/.

## Security and operations

Keep all store tokens, Gmail credentials, customer emails, private product exports, and order files out of Git. The project supplies .env.example as documentation only. Obtain independently authorized Shopify or Gmail credentials, restrict their scopes, and verify each integration against an authorized test environment. Existing preview/approval steps remain mandatory for writes; return processing remains offline review-only, and Gmail assistance only creates drafts after approval.

The installer does not install or configure optional background schedules, public feeds, refunds, message sending, or access to customer data. Test each capability end-to-end before claiming it is production-ready. OpenClaw may execute powerful tools; review its security and sandbox configuration and use minimum necessary privileges.

## Troubleshooting

If the installer says OpenClaw is missing after onboarding, reopen Terminal, verify your PATH, and rerun bash install.sh. For file conflicts, back up the workspace and compare versions; the installer will not automatically overwrite or merge different content. If OpenClaw does not display skills, verify the active workspace path and follow the official skills documentation for the installed OpenClaw version.
