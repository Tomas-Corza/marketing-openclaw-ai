# Cloud Business AI Agent

A **browser-accessible custom Python agent prototype** built on the Marketing OpenClaw AI portfolio concept. This is **not** a deployment of the official OpenClaw runtime. It runs without installing anything on a personal computer when hosted through Streamlit Community Cloud or another Python web-app host.

## What it does

- Provides a conversational interface for marketing, e-commerce, and finance reviews.
- Lets visitors choose among three inspectable **fictional** business datasets.
- Sends the selected sample data and question to a configurable OpenAI model.
- Returns a read-only analysis with suggested next steps.
- Does **not** call third-party business APIs, send emails, write financial records, or execute shell commands.

## Deploy entirely from a web browser (Streamlit Community Cloud)

1. Open [share.streamlit.io](https://share.streamlit.io/) and sign in with GitHub.
2. Select this repository and the branch containing these files (or merge the pull request into `main` first).
3. Set the main file path to `cloud_agent/app.py`.
4. In the app's **Secrets** settings, set `OPENAI_API_KEY` to your provider key. Do **not** commit real keys to GitHub. Streamlit secrets are not automatically environment variables: for this app, use a host environment variable or adapt the code to read `st.secrets` (see below).
5. Deploy and open the generated URL. The code still loads without a key, but model responses require a working API key and provider billing.

### Streamlit secret configuration

Set the Streamlit secrets entry below instead of exposing an API key in the repository:

```toml
OPENAI_API_KEY = "your-key-here"
```

The app reads this value through `st.secrets` as a fallback when supported. Secrets should be managed in your Streamlit deployment dashboard.

## Run in GitHub Codespaces instead

Open repository → **Code** → **Codespaces** → **Create codespace**. In the browser terminal:

```bash
pip install -r cloud_agent/requirements.txt
streamlit run cloud_agent/app.py --server.address 0.0.0.0
```

Use Codespaces' **Ports** panel to open port 8501. Set your API key as a Codespaces secret/environment variable. Codespaces are development environments, not guaranteed always-on hosting.

## Limits and next steps

This is a focused, read-only agent demo. It does not yet invoke the repository's business tools as callable skills. Future integrations should use scoped credentials, approved tool-call registries, audit logs, and a human approval step before any data modification. Protect access and implement authentication before connecting private business data.
