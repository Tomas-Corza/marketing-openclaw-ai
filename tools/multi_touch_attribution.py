#!/usr/bin/env python3
"""Offline rule-based multi-touch attribution for pre-linked, consented journeys."""
import argparse
import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

MODELS = ("first_touch", "last_touch", "linear", "position_based", "time_decay")


def parse_time(value):
    try:
        dt = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Invalid ISO-8601 timestamp: " + str(value)) from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("All timestamps require an explicit timezone offset")
    return dt.astimezone(timezone.utc)


def parse_revenue(value):
    try:
        amount = Decimal(str(value))
        if not amount.is_finite() or amount < 0 or amount != amount.quantize(Decimal("0.01")):
            raise ValueError("Revenue must be a nonnegative amount in cents")
        return amount
    except InvalidOperation as exc:
        raise ValueError("Invalid revenue amount") from exc


def read_csv(path, required):
    with open(path, newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        missing = set(required) - set(reader.fieldnames or [])
        if missing:
            raise ValueError("Missing required fields: " + ", ".join(sorted(missing)))
        return list(reader)


def normalize(touchpoints, conversions):
    seen_touches, seen_orders = set(), set()
    touches, orders = [], []
    for row in touchpoints:
        tid, cid, channel = (str(row[k]).strip() for k in ("touchpoint_id", "customer_id", "channel"))
        if not all((tid, cid, channel)) or tid in seen_touches:
            raise ValueError("Touchpoints require nonblank fields and unique touchpoint_id")
        seen_touches.add(tid)
        touches.append(dict(touchpoint_id=tid, customer_id=cid, channel=channel,
                            occurred_at=parse_time(row["occurred_at"])))
    for row in conversions:
        oid, cid = (str(row[k]).strip() for k in ("conversion_id", "customer_id"))
        if not oid or not cid or oid in seen_orders:
            raise ValueError("Conversions require unique conversion_id and customer_id")
        seen_orders.add(oid)
        orders.append(dict(conversion_id=oid, customer_id=cid,
                           converted_at=parse_time(row["converted_at"]), revenue=parse_revenue(row["revenue"])))
    return touches, orders


def model_weights(touches, converted_at, model, half_life_days):
    n = len(touches)
    if model == "first_touch":
        raw = [1.0] + [0.0] * (n - 1)
    elif model == "last_touch":
        raw = [0.0] * (n - 1) + [1.0]
    elif model == "linear":
        raw = [1.0] * n
    elif model == "position_based":
        raw = [1.0] if n == 1 else ([0.5, 0.5] if n == 2 else [0.4] + [0.2 / (n - 2)] * (n - 2) + [0.4])
    elif model == "time_decay":
        raw = [math.exp(-math.log(2) * (converted_at - t["occurred_at"]).total_seconds() / 86400 / half_life_days)
               for t in touches]
    else:
        raise ValueError("Unsupported model")
    total = sum(raw)
    return [value / total for value in raw]


def cents_by_largest_remainder(amount, shares):
    """Distribute integer cents without inventing or losing revenue."""
    total_cents = int(amount * 100)
    raw = [Decimal(str(share)) * total_cents for share in shares]
    cents = [int(value) for value in raw]
    remainder = total_cents - sum(cents)
    ranked = sorted(range(len(raw)), key=lambda index: (-(raw[index] - cents[index]), index))
    for index in ranked[:remainder]:
        cents[index] += 1
    return cents


def attribute(touchpoints, conversions, model="linear", lookback_days=30, half_life_days=7):
    if model not in MODELS:
        raise ValueError("Invalid model")
    if not 1 <= lookback_days <= 365:
        raise ValueError("lookback_days must be 1 to 365")
    if not math.isfinite(half_life_days) or half_life_days <= 0:
        raise ValueError("half_life_days must be positive and finite")
    touches, orders = normalize(touchpoints, conversions)
    by_customer = defaultdict(list)
    for touch in touches:
        by_customer[touch["customer_id"]].append(touch)
    for journey in by_customer.values():
        journey.sort(key=lambda t: (t["occurred_at"], t["touchpoint_id"]))
    rows, audits = [], []
    channels = defaultdict(lambda: dict(cents=0, conversion_credit=0.0))
    for order in sorted(orders, key=lambda item: (item["converted_at"], item["conversion_id"])):
        earliest = order["converted_at"] - timedelta(days=lookback_days)
        journey = [touch for touch in by_customer[order["customer_id"]]
                   if earliest <= touch["occurred_at"] <= order["converted_at"]]
        audits.append(dict(conversion_id=order["conversion_id"], touchpoint_count=len(journey),
                           status="attributed" if journey else "unattributed", revenue=str(order["revenue"])))
        if not journey:
            continue
        shares = model_weights(journey, order["converted_at"], model, half_life_days)
        cents = cents_by_largest_remainder(order["revenue"], shares)
        for touch, share, amount in zip(journey, shares, cents):
            rows.append(dict(conversion_id=order["conversion_id"], touchpoint_id=touch["touchpoint_id"],
                             channel=touch["channel"], weight=round(share, 12),
                             attributed_revenue=f"{Decimal(amount) / 100:.2f}"))
            channels[touch["channel"]]["cents"] += amount
            channels[touch["channel"]]["conversion_credit"] += share
    total_revenue = sum((order["revenue"] for order in orders), Decimal("0.00"))
    assigned = sum((Decimal(row["attributed_revenue"]) for row in rows), Decimal("0.00"))
    return dict(
        model=model, lookback_days=lookback_days, half_life_days=half_life_days if model == "time_decay" else None,
        totals=dict(total_conversions=len(orders),
                    attributed_conversions=sum(a["status"] == "attributed" for a in audits),
                    unattributed_conversions=sum(a["status"] == "unattributed" for a in audits),
                    total_revenue=f"{total_revenue:.2f}", attributed_revenue=f"{assigned:.2f}",
                    unattributed_revenue=f"{total_revenue - assigned:.2f}"),
        conversions=audits, allocations=rows,
        channels=[dict(channel=name, attributed_revenue=f"{Decimal(item['cents']) / 100:.2f}",
                       conversion_credit=round(item["conversion_credit"], 12))
                  for name, item in sorted(channels.items())],
        limitation="Descriptive rule-based credit, not causal lift or universal cross-device tracking.",
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--touchpoints", type=Path, required=True)
    parser.add_argument("--conversions", type=Path, required=True)
    parser.add_argument("--model", choices=MODELS, default="linear")
    parser.add_argument("--lookback-days", type=int, default=30)
    parser.add_argument("--half-life-days", type=float, default=7)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = attribute(
        read_csv(args.touchpoints, ("touchpoint_id", "customer_id", "channel", "occurred_at")),
        read_csv(args.conversions, ("conversion_id", "customer_id", "converted_at", "revenue")),
        args.model, args.lookback_days, args.half_life_days)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("Wrote", args.output)


if __name__ == "__main__":
    main()
