"""Synthetic, read-only marketing attribution dashboard.

No API calls, uploads, tracking, credentials or real merchant data.
Uses the same offline Shopify+GA4 pipeline as the command-line tools.
"""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from tools.shopify_ga4_pipeline import prepare

ROOT = Path(__file__).resolve().parents[1]
EVENTS = ROOT / "examples" / "ga4_bigquery_events.csv"
ORDERS = ROOT / "examples" / "shopify_attribution_orders.csv"
MODELS = {
    "Linear": "linear",
    "First touch": "first_touch",
    "Last touch": "last_touch",
    "Position-based (40 / 20 / 40)": "position_based",
    "Time decay": "time_decay",
}


def fixture_rows(path: Path) -> list[dict]:
    """Read bundled synthetic fixtures, not user-uploaded files."""
    return list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"))))


def run_demo(model: str, lookback_days: int, half_life_days: float) -> dict:
    return prepare(fixture_rows(EVENTS), fixture_rows(ORDERS), model, lookback_days, half_life_days)


def comparison_rows(lookback_days: int, half_life_days: float) -> list[dict]:
    """Compare revenue credit by channel under each model, without adding credits together."""
    rows = []
    for label, model in MODELS.items():
        result = run_demo(model, lookback_days, half_life_days)
        for channel in result["channels"]:
            rows.append({
                "Attribution model": label,
                "Channel": channel["channel"],
                "Attributed revenue (USD)": float(channel["attributed_revenue"]),
                "Fractional conversions": round(channel["conversion_credit"], 3),
            })
    return rows


def render_attribution_tab(st) -> None:
    st.subheader("Customer-journey ad attribution")
    st.caption("Interactive rule-based attribution on synthetic Shopify orders and consented GA4 events. No live accounts connected.")
    left, middle, right = st.columns([2, 1, 1])
    with left:
        selection = st.selectbox("Credit-allocation model", list(MODELS), index=0, key="attr_model")
    with middle:
        window = st.slider("Lookback (days)", min_value=1, max_value=90, value=30, key="attr_lookback")
    with right:
        half_life = st.number_input("Time-decay half-life (days)", min_value=0.5, max_value=60.0,
                                    value=7.0, step=0.5, disabled=selection != "Time decay", key="attr_half_life")
    report = run_demo(MODELS[selection], window, half_life)
    audit = report["pipeline_audit"]
    totals = report["totals"]

    st.markdown("#### Shopify → GA4 → attribution")
    cols = st.columns(4)
    cols[0].metric("Shopify orders", audit["total_shopify_orders"])
    cols[1].metric("Matched GA4 purchases", audit["ga4_matched_orders"])
    cols[2].metric("Orders with credited touchpoints", audit["attributed_orders"])
    cols[3].metric("Attributed revenue (USD)", f'${float(totals["attributed_revenue"]):,.2f}')
    st.caption(
        f'Synthetic store revenue: ${float(audit["total_shopify_revenue"]):,.2f}. '
        f'Orders without verified purchase matches: {audit["orders_without_verified_purchase_match"]}. '
        f'Ambiguous purchase matches: {audit["ambiguous_order_count"]}. '
        f'Matched orders without eligible touchpoints: {audit["matched_orders_without_eligible_touchpoints"]}. '
        "Unmatched orders are excluded from credit allocation."
    )
    st.markdown("#### Channel credit")
    if report["channels"]:
        chart_data = {
            row["channel"]: float(row["attributed_revenue"]) for row in report["channels"]
        }
        st.bar_chart({"Attributed revenue (USD)": chart_data})
        st.dataframe(
            [
                {
                    "Channel": row["channel"],
                    "Revenue credit (USD)": float(row["attributed_revenue"]),
                    "Conversion credit": round(row["conversion_credit"], 3),
                }
                for row in report["channels"]
            ],
            hide_index=True, width="stretch",
        )
    else:
        st.info("No eligible touchpoints for this model and lookback window.")

    st.markdown("#### How the attribution model changes channel credit")
    st.caption("Each model independently allocates the same eligible order revenue; do not sum results across models.")
    comparisons = comparison_rows(window, half_life)
    st.dataframe(comparisons, hide_index=True, width="stretch")

    st.markdown("#### Auditable customer journeys")
    available = [row["conversion_id"] for row in report["conversions"]]
    if available:
        chosen_order = st.selectbox("Inspect a matched Shopify order", available, key="attr_order")
        order_audit = next(row for row in report["conversions"] if row["conversion_id"] == chosen_order)
        st.write(
            f'**{chosen_order}** · {order_audit["status"]} · '
            f'{order_audit["touchpoint_count"]} eligible touchpoints · '
            f'${float(order_audit["revenue"]):,.2f} order revenue'
        )
        selected = [row for row in report["allocations"] if row["conversion_id"] == chosen_order]
        if selected:
            st.dataframe(selected, hide_index=True, width="stretch")
        else:
            st.info("This order has no creditable touchpoints in the synthetic dataset.")

    st.download_button(
        "Download synthetic attribution report (JSON)",
        json.dumps(report, indent=2).encode("utf-8"),
        "synthetic-shopify-ga4-attribution.json",
        mime="application/json",
        key="attr_download",
    )
    with st.expander("What is required for genuine multi-touch attribution?"):
        st.markdown(
            "A legitimate GA4 BigQuery event export with consented first-party interactions, "
            "a consistent browser identifier, and purchase events containing transaction IDs "
            "that **exactly match** Shopify order IDs. Shopify order exports must also contain "
            "timestamps, revenue, and currency. Configure tracking and authorized data access separately. "
            "The pipeline doesn't discover cross-device identities, infer unobserved touches, or measure causal lift."
        )
        st.markdown(
            "[Source and setup guide](https://github.com/Tomas-Corza/marketing-openclaw-ai/blob/feature/customer-journey-multi-touch-attribution/docs/shopify-ga4-bigquery-pipeline.md) "
            "· [Attribution engine](https://github.com/Tomas-Corza/marketing-openclaw-ai/blob/feature/customer-journey-multi-touch-attribution/tools/multi_touch_attribution.py)"
        )
    st.info(
        "Portfolio demonstration only. All touchpoints, customers and revenue shown here are synthetic. "
        "The model assigns descriptive revenue credit, not proven ad impact."
    )
