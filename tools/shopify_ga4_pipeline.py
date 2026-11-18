"""Offline GA4 BigQuery CSV + Shopify orders => rule-based multi-touch report.

Only a consented GA4 purchase with transaction_id matching Shopify order_id
links the preceding GA4 pseudo-ID journey to revenue. No identity stitching.
"""
import argparse
import csv
import json
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
try:
    from tools.multi_touch_attribution import attribute, parse_time, parse_revenue
except ModuleNotFoundError:
    # Direct invocation: python3 tools/shopify_ga4_pipeline.py
    from multi_touch_attribution import attribute, parse_time, parse_revenue

GA4 = {"event_id","user_pseudo_id","event_name","occurred_at","channel","transaction_id","analytics_storage"}
ORDERS = {"order_id","converted_at","revenue","currency"}

def load(path, fields):
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = fields - set(reader.fieldnames or [])
        if missing:
            raise ValueError("Missing columns: " + ", ".join(sorted(missing)))
        return list(reader)

def prepare(events, orders, model="linear", lookback_days=30, half_life_days=7):
    indexed, currencies = {}, set()
    for row in orders:
        oid = str(row["order_id"]).strip()
        if not oid or oid in indexed:
            raise ValueError("Order IDs must be unique and nonblank")
        currency = str(row["currency"]).strip().upper()
        if len(currency) != 3 or not currency.isalpha():
            raise ValueError("Currency must be a three-letter code")
        currencies.add(currency)
        indexed[oid] = {"when":parse_time(row["converted_at"]), "revenue":parse_revenue(row["revenue"])}
    if len(currencies) > 1:
        raise ValueError("Convert mixed currencies before attribution")

    clean, seen = [], set()
    for row in events:
        eid = str(row["event_id"]).strip()
        if not eid or eid in seen:
            raise ValueError("GA4 event IDs must be unique and nonblank")
        seen.add(eid)
        when = parse_time(row["occurred_at"])
        ga_id = str(row["user_pseudo_id"]).strip()
        if str(row["analytics_storage"]).strip().lower() != "yes" or not ga_id:
            continue
        clean.append({"id":eid,"uid":ga_id,"when":when, "name":str(row["event_name"]).strip(),
                      "channel":str(row["channel"]).strip(),
                      "tx":str(row["transaction_id"]).strip()})
    candidates = defaultdict(set)
    for ev in clean:
        if ev["name"] == "purchase" and ev["tx"] in indexed:
            if abs((ev["when"] - indexed[ev["tx"]]["when"]).total_seconds()) <= 86400:
                candidates[ev["tx"]].add(ev["uid"])
    linked = {oid:next(iter(ids)) for oid,ids in candidates.items() if len(ids) == 1}
    ambiguous = sorted(oid for oid,ids in candidates.items() if len(ids) > 1)
    conversions = [{"conversion_id":oid,"customer_id":uid,
                    "converted_at":indexed[oid]["when"].isoformat(),
                    "revenue":str(indexed[oid]["revenue"])} for oid,uid in linked.items()]
    ids = set(linked.values())
    touches = [{"touchpoint_id":ev["id"],"customer_id":ev["uid"],
                "occurred_at":ev["when"].isoformat(),"channel":ev["channel"]}
               for ev in clean if ev["uid"] in ids and ev["name"] in ("page_view","session_start")
               and ev["channel"] and ev["channel"].lower() not in ("direct","(direct)","unknown","unassigned")]
    report = attribute(touches, conversions, model, lookback_days, half_life_days)
    qualifying = sum(row["status"] == "attributed" for row in report["conversions"])
    report["pipeline_audit"] = {
        "currency":next(iter(currencies),None),
        "total_shopify_orders":len(indexed),
        "total_shopify_revenue":str(sum((o["revenue"] for o in indexed.values()),Decimal("0.00"))),
        "ga4_matched_orders":len(linked),
        "ambiguous_order_count":len(ambiguous),
        "orders_without_verified_purchase_match":len(indexed)-len(linked)-len(ambiguous),
        "matched_orders_without_eligible_touchpoints":len(linked)-qualifying,
        "attributed_orders":qualifying,
        "note":"Only consented, observable, same-GA4-identifier journeys. Missing orders are not assigned credit.",
    }
    return report

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ga4-events",type=Path,required=True)
    p.add_argument("--shopify-orders",type=Path,required=True)
    p.add_argument("--model",choices=("first_touch","last_touch","linear","position_based","time_decay"),default="linear")
    p.add_argument("--lookback-days",type=int,default=30)
    p.add_argument("--half-life-days",type=float,default=7)
    p.add_argument("--output",type=Path,required=True)
    a = p.parse_args()
    result = prepare(load(a.ga4_events,GA4),load(a.shopify_orders,ORDERS),
                     a.model,a.lookback_days,a.half_life_days)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("Wrote",a.output)

if __name__ == "__main__":
    main()
