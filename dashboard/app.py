"""Interactive local e-commerce operations control center.

Launch from the repository root:
    streamlit run dashboard/app.py

No live API writes and no background jobs are initiated by this dashboard.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from dashboard.attribution_view import render_attribution_tab
from dashboard.logic import (
    EDITABLE_FIELDS, approval_manifest, json_bytes, locally_reviewed_preview,
    parse_catalog, parse_feed, queue_change, read_optional_json,
    run_diagnostics, source_fingerprint, summarize, tsv_bytes,
)

DEMO = ROOT / "examples" / "dashboard"
PUBLIC_DEMO = os.getenv("OPENCLAW_PUBLIC_DEMO", "").strip() == "1"

st.set_page_config(page_title="Marketing OpenClaw | E-Commerce & Attribution", page_icon="📊", layout="wide")
st.title("E-Commerce Operations & Attribution")
st.caption("Marketing OpenClaw AI · Shopify operations, feed diagnostics and customer-journey attribution")
if PUBLIC_DEMO:
    st.info("Public portfolio demo · All products, AI drafts, marketing touchpoints and order revenue are synthetic. No real store or ad account is connected.")

with st.sidebar:
    st.header("Workspace")
    demo_mode = True if PUBLIC_DEMO else st.toggle("Synthetic demonstration data", value=True)
    st.caption("Public synthetic-only mode · uploads disabled." if PUBLIC_DEMO else "No store account is connected by this application.")
    if demo_mode:
        catalog_bytes = (DEMO / "shopify_catalog.csv").read_bytes()
        feed_bytes = (DEMO / "merchant_feed.tsv").read_bytes()
        feed_name = "merchant_feed.tsv"
        ai_bytes = (DEMO / "ai_drafts.json").read_bytes()
        merchant_bytes = (DEMO / "merchant_status.json").read_bytes()
        st.success("Synthetic examples loaded")
    else:
        csv_upload = st.file_uploader("Shopify catalog CSV", type=["csv"])
        feed_upload = st.file_uploader("Merchant feed TSV or RSS", type=["tsv", "txt", "rss", "xml"])
        ai_upload = st.file_uploader("AI draft JSON (optional)", type=["json"], key="ai")
        merchant_upload = st.file_uploader("Merchant status JSON (optional)", type=["json"], key="merchant")
        if csv_upload is None or feed_upload is None:
            st.info("Upload an authorized Shopify CSV and Merchant feed to continue.")
            st.stop()
        catalog_bytes = csv_upload.getvalue()
        feed_bytes = feed_upload.getvalue()
        feed_name = feed_upload.name
        ai_bytes = ai_upload.getvalue() if ai_upload else None
        merchant_bytes = merchant_upload.getvalue() if merchant_upload else None
    st.divider()
    st.warning("Demo-only local previews — no Shopify, Merchant Center, or AI API calls.", icon="🔒")
    if PUBLIC_DEMO:
        st.markdown("[View source code](https://github.com/Tomas-Corza/marketing-openclaw-ai) · [Portfolio](https://tomascorza.me/ai-marketing-analytics)")

try:
    catalog = parse_catalog(catalog_bytes)
    items = parse_feed(feed_bytes, feed_name)
    ai_report = read_optional_json(ai_bytes, "items")
    merchant_status = read_optional_json(merchant_bytes, "products")
    diagnostics = run_diagnostics(items, merchant_status)
except (ValueError, OSError, json.JSONDecodeError, UnicodeError) as exc:
    st.error(f"Cannot analyze uploaded files: {exc}")
    st.stop()

fingerprint = source_fingerprint(catalog_bytes, feed_bytes, ai_bytes or b"", merchant_bytes or b"")
if st.session_state.get("input_fingerprint") != fingerprint:
    # Stale approvals must never carry over to a different catalog/feed snapshot.
    for widget_key in list(st.session_state.keys()):
        if widget_key.startswith("review_"):
            del st.session_state[widget_key]
    st.session_state["input_fingerprint"] = fingerprint
    st.session_state["staged_edits"] = {}
    st.session_state["approved_offer_ids"] = set()
    st.session_state["event_log"] = []

def event(label: str, detail: str):
    st.session_state["event_log"].append({
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "event": label,
        "detail": detail,
    })

overview, products, feed_health, attribution, queue, history = st.tabs([
    "Overview", "Product Optimization", "Merchant Feed Health", "Ad Attribution", "Approval Queue", "Activity",
])

with overview:
    metrics = summarize(catalog, diagnostics, ai_report)
    columns = st.columns(4)
    columns[0].metric("Catalog products", metrics["catalog_products"])
    columns[1].metric("Feed offers", metrics["feed_products"])
    columns[2].metric("Feed issues", metrics["feed_issues"])
    columns[3].metric("Critical issues", metrics["critical_issues"])
    left, right = st.columns(2)
    with left:
        st.subheader("Issues by priority")
        priorities = diagnostics["issue_counts"]
        st.bar_chart({"Issues": {severity: priorities.get(severity, 0)
                                  for severity in ("critical", "high", "medium", "low")}})
    with right:
        st.subheader("Work awaiting review")
        st.metric("Shopify content findings", metrics["catalog_findings"])
        st.metric("AI copy drafts", metrics["ai_drafts"])
        st.metric("Staged local feed fixes", len(st.session_state["staged_edits"]))
        if diagnostics.get("merchant_disapproved_products") is not None:
            st.metric("Disapproved in supplied Merchant snapshot", diagnostics["merchant_disapproved_products"])
    st.info("Demo values are synthetic. An imported status snapshot is not a real-time Merchant API connection.")

with products:
    st.subheader("Shopify catalog audit")
    st.caption("Powered by the existing Shopify bulk feed audit module.")
    st.dataframe(catalog["audit"], hide_index=True, width="stretch")
    st.download_button("Export Shopify audit", json_bytes(catalog),
                       "shopify-catalog-audit.json", "application/json")
    st.divider()
    st.subheader("AI-generated content drafts")
    drafts = [item for item in (ai_report or {}).get("items", []) if "suggested_changes" in item]
    if drafts:
        choice = st.selectbox("Choose a product draft", range(len(drafts)),
                              format_func=lambda i: str(drafts[i].get("handle", "Unidentified")))
        current, proposed = st.columns(2)
        with current:
            st.markdown("**Provided source content**")
            st.json(drafts[choice].get("original", {}))
        with proposed:
            st.markdown("**AI suggestion — unverified**")
            st.json(drafts[choice]["suggested_changes"])
        st.caption(f"JTBD hypothesis: {drafts[choice].get('jtbd_hypothesis', 'Not supplied')}")
        st.warning("AI content is never approved for Shopify publishing here. Verify merchant facts and Product IDs through a separate workflow.")
    else:
        st.info("Optional: upload an AI draft report generated by tools/shopify_ai_copy.py.")

with feed_health:
    st.subheader("Feed issue diagnostics")
    severity = st.multiselect("Priority", ["critical", "high", "medium", "low"],
                              default=["critical", "high", "medium", "low"])
    filtered = [item for item in diagnostics["issues"] if item["priority"] in severity]
    if filtered:
        st.dataframe(filtered, hide_index=True, width="stretch")
    else:
        st.info("No matching issues from these offline checks. Approval by Merchant Center is not guaranteed.")
    st.download_button("Export diagnostics", json_bytes(diagnostics),
                       "merchant-diagnostics.json", "application/json")

with attribution:
    render_attribution_tab(st)

with queue:
    st.subheader("Approval queue — downloadable feed fixes")
    st.caption("Allowed fields: title, description, link, image_link, brand, gtin and mpn. Never price, inventory, availability or IDs.")
    choices = sorted(set(item.get("id", "") for item in items if item.get("id")))
    if choices:
        with st.form("stage_correction", clear_on_submit=True):
            offer = st.selectbox("Existing offer ID", choices)
            field = st.selectbox("Attribute", EDITABLE_FIELDS)
            replacement = st.text_area("Proposed merchant-verified replacement")
            checked = st.checkbox("I verified this exact value against authoritative product data")
            stage = st.form_submit_button("Stage for review")
        if stage:
            if not checked:
                st.error("Verify the replacement value before staging.")
            else:
                try:
                    st.session_state["staged_edits"] = queue_change(
                        items, st.session_state["staged_edits"], offer, field, replacement,
                    )
                    st.session_state["approved_offer_ids"].discard(offer)
                    # Reset the existing widget key after the proposal changes.
                    st.session_state.pop(f"review_{offer}", None)
                    event("Change staged", f"{offer}: {field}; approval reset")
                    st.success("Staged for review; nothing published.")
                except ValueError as exc:
                    st.error(str(exc))
    else:
        st.warning("No valid offer IDs are present.")

    staged = st.session_state["staged_edits"]
    if staged:
        st.markdown("#### Review each proposed edit")
        for ident, patch in list(staged.items()):
            with st.expander(f"{ident} · {'Approved' if ident in st.session_state['approved_offer_ids'] else 'Pending'}"):
                item = next(record for record in items if record["id"] == ident)
                old, new = st.columns(2)
                old.json({k: item.get(k, "") for k in patch})
                new.json(patch)
                approved = st.checkbox("Approve exact correction for local feed export",
                                       value=ident in st.session_state["approved_offer_ids"],
                                       key=f"review_{ident}")
                if approved and ident not in st.session_state["approved_offer_ids"]:
                    st.session_state["approved_offer_ids"].add(ident)
                    event("Local change approved", ident)
                elif not approved and ident in st.session_state["approved_offer_ids"]:
                    st.session_state["approved_offer_ids"].remove(ident)
                    event("Local approval revoked", ident)
                if st.button("Remove staged change", key=f"delete_{ident}"):
                    staged.pop(ident)
                    st.session_state["approved_offer_ids"].discard(ident)
                    st.session_state.pop(f"review_{ident}", None)
                    event("Change removed", ident)
                    st.rerun()
        manifest = approval_manifest(items, staged, st.session_state["approved_offer_ids"])
        st.download_button("Export review manifest", json_bytes(manifest),
                           "feed-review-manifest.json", "application/json")
        if all(entry["approved"] for entry in manifest):
            try:
                reviewed = locally_reviewed_preview(items, manifest)
                st.download_button("Export approved local TSV", tsv_bytes(reviewed),
                                   "approved-feed-preview.tsv", "text/tab-separated-values")
                st.success("Changes approved for **local file export only**. No live feed has been updated.")
            except ValueError as exc:
                st.error(str(exc))
        else:
            st.info("All staged offers must be individually approved to export a corrected local feed.")
    else:
        st.info("No feed corrections staged. Inspect the diagnostics and enter source-verified changes.")

with history:
    st.subheader("Activity in this browser session")
    st.caption("This is not persistent audit storage or live automation execution history.")
    if st.session_state["event_log"]:
        st.dataframe(list(reversed(st.session_state["event_log"])), hide_index=True, width="stretch")
        st.download_button("Export session event log", json_bytes(st.session_state["event_log"]),
                           "session-activity.json", "application/json")
    else:
        st.info("Review events will appear as changes are staged and approved.")
    st.subheader("Other automation modules")
    st.markdown("""
    **Existing repository commands** (not executed automatically by this dashboard):
    - Shopify bulk content audit: `tools/shopify_bulk_feed.py`
    - AI product copy generation: `tools/shopify_ai_copy.py`
    - Product feed builder and sync: `tools/shopify_feed_builder.py`, `tools/shopify_live_feed_sync.py`
    - Merchant diagnostics and API connector: `tools/merchant_feed_diagnostics.py`, `tools/merchant_api_connector.py`
    - Shopify/GA4 attribution: `tools/shopify_ga4_pipeline.py`, `tools/multi_touch_attribution.py`
    """)
