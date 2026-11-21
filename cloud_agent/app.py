"""Browser-based, read-only business AI agent demo. No local installation required."""
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import streamlit as st

st.set_page_config(page_title="Cloud Business AI Agent", page_icon="☁️", layout="centered")
st.title("☁️ Cloud Business AI Agent")
st.caption("Marketing OpenClaw AI · browser-based prototype · synthetic business data")
st.info("This is a custom Python agent demo, not the official OpenClaw gateway. It cannot access live stores, banks, or inboxes and cannot make changes to business systems.")

SAMPLE = {
    "Marketing performance": {
        "period": "Fictional 7-day sample",
        "revenue_usd": 18420,
        "orders": 94,
        "ad_spend_usd": 5120,
        "attributed_ad_revenue_usd": 12980,
        "channel_roas": {"Search": 3.2, "Paid social": 1.8},
        "notes": ["Attribution is illustrative, not incrementality.", "Results use entirely synthetic records."],
    },
    "E-commerce operations": {
        "period": "Fictional inventory snapshot",
        "active_products": 138,
        "out_of_stock_products": 17,
        "products_missing_meta_descriptions": 23,
        "drafts_requiring_review": 8,
        "notes": ["No live Shopify store is connected.", "No updates are performed."],
    },
    "Finance exceptions": {
        "period": "Fictional month-end snapshot",
        "unmatched_bank_transactions": 6,
        "overdue_receivables_usd": 7400,
        "invoices_requiring_manual_review": 3,
        "notes": ["Not accounting advice.", "No QuickBooks, payroll, or banking integration is connected."],
    },
}
SYSTEM = (
    "You are a careful business operations assistant. You are analyzing only fictional sample data. "
    "Never imply access to real accounts, live tools, or actual systems. "
    "Clearly distinguish observed values from hypothetical recommendations. "
    "Do not claim to have executed external actions. State when data is insufficient. "
    "Provide short practical business recommendations."
)

def get_response(question: str, dataset: dict, history: list[dict]) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()\n    if not api_key:\n        try:\n            api_key = str(st.secrets.get("OPENAI_API_KEY", "")).strip()\n        except (FileNotFoundError, KeyError):\n            api_key = ""
    if not api_key:
        return ("No model API key is configured. The synthetic dataset is available below. "
                "To enable AI responses, add OPENAI_API_KEY as a secret in your hosting platform.")
    payload = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "system", "content": "Synthetic report (JSON): " + json.dumps(dataset)},
            *history[-8:],
            {"role": "user", "content": question},
        ],
        "temperature": 0.2,
        "max_tokens": 650,
    }
    req = Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=35) as response:
            data = json.load(response)
        return data["choices"][0]["message"]["content"]
    except HTTPError as exc:
        if exc.code in (401, 403):
            return "The model provider rejected the configured API credentials or permissions. Check server secrets."
        if exc.code == 429:
            return "The model provider is rate-limiting requests or the account has insufficient quota."
        return f"Model request failed (HTTP {exc.code}). Check server logs."
    except (URLError, TimeoutError, KeyError, ValueError):
        return "Could not complete the model request. Please retry or check the deployment logs."

selected = st.selectbox("Choose a business workflow", list(SAMPLE))
dataset = SAMPLE[selected]
with st.expander("Inspect synthetic source data", expanded=True):
    st.json(dataset)
st.caption("Read-only • no commands or integrations • API secrets stay server-side")
if st.session_state.get("selected") != selected:
    st.session_state.selected = selected
    st.session_state.messages = []
for message in st.session_state.get("messages", []):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
question = st.chat_input("Ask for an analysis, exceptions, or recommendations")
if question:
    prior = list(st.session_state.messages)
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("Analyzing synthetic records…"):
            response = get_response(question, dataset, prior)
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
