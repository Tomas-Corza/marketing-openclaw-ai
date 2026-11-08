#!/usr/bin/env python3
"""Offline, cross-platform social content engagement summary. Standard library only."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from social_behavior_connector import CSVConnector

REQUIRED = ("platform", "content_id", "published_at", "impressions", "likes", "comments", "shares", "saves", "clicks")
COUNTS = ("impressions", "likes", "comments", "shares", "saves", "clicks", "views", "reach")
OPTIONAL = ("content_type", "topic", "campaign", "source_url")


def parse_timestamp(value: str) -> None:
    if not value:
        raise ValueError("published_at cannot be empty")
    datetime.fromisoformat(value.replace("Z", "+00:00"))


def parse_count(value: object, field: str) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    value = str(value).strip()
    if not value.isdecimal():
        raise ValueError(f"{field} must be a nonnegative integer or blank, got {value!r}")
    return int(value)


def read_records(path: str) -> list[dict]:
    rows = list(CSVConnector(path).fetch())
    if not rows:
        raise ValueError("Input has no records")
    missing = set(REQUIRED) - set(rows[0])
    if missing:
        raise ValueError("Missing columns: " + ", ".join(sorted(missing)))
    records, seen = [], set()
    for index, raw in enumerate(rows, 2):
        try:
            record = {key: str(raw.get(key) or "").strip() for key in ("platform", "content_id", "published_at") + OPTIONAL}
            for key in ("platform", "content_id"):
                if not record[key]:
                    raise ValueError(f"{key} cannot be empty")
            parse_timestamp(record["published_at"])
            identity = (record["platform"].lower(), record["content_id"])
            if identity in seen:
                raise ValueError("duplicate platform/content_id (provide one row per content item)")
            seen.add(identity)
            for key in COUNTS:
                record[key] = parse_count(raw.get(key), key)
            records.append(record)
        except ValueError as exc:
            raise ValueError(f"CSV row {index}: {exc}") from exc
    return records


def aggregate(records: list[dict]) -> dict:
    sums = {key: sum(r[key] for r in records if r[key] is not None) for key in COUNTS}
    known = {key: sum(r[key] is not None for r in records) for key in COUNTS}
    def rate(numerators: tuple[str, ...]) -> float | None:
        eligible = [r for r in records if r["impressions"] is not None and all(r[k] is not None for k in numerators)]
        if not eligible or sum(r["impressions"] for r in eligible) == 0:
            return None
        return round(sum(sum(r[k] for k in numerators) for r in eligible) / sum(r["impressions"] for r in eligible), 6)
    return {
        "content_count": len(records),
        "total_observed": sums,
        "coverage_by_metric": known,
        "engagement_per_impression": rate(("likes", "comments", "shares", "saves")),
        "clicks_per_impression": rate(("clicks",)),
    }


def analyze(records: list[dict]) -> dict:
    platforms = defaultdict(list)
    types = defaultdict(list)
    topics = defaultdict(list)
    for record in records:
        platforms[record["platform"]].append(record)
        if record["content_type"]:
            types[(record["platform"], record["content_type"])].append(record)
        if record["topic"]:
            topics[(record["platform"], record["topic"])].append(record)
    return {
        "report_type": "social_behavior_monitor",
        "scope": "Aggregated content-level engagement; no individual behavior tracking",
        "date_range": {
            "earliest_published_at": min(r["published_at"] for r in records),
            "latest_published_at": max(r["published_at"] for r in records),
        },
        "overall": aggregate(records),
        "by_platform": {p: aggregate(rs) for p, rs in sorted(platforms.items())},
        "by_platform_and_content_type": [
            {"platform": p, "content_type": t, **aggregate(rs)} for (p, t), rs in sorted(types.items())
        ],
        "by_platform_and_topic": [
            {"platform": p, "topic": t, **aggregate(rs)} for (p, t), rs in sorted(topics.items())
        ],
        "limitations": [
            "API integrations are not configured; this report uses a local CSV export.",
            "Different platforms may define metrics differently; avoid comparing raw rates across platforms.",
            "Unknown metrics are omitted from corresponding rate calculations rather than assumed zero.",
            "Content-level associations do not prove causes, motivations, or future behavior.",
            "Published-at dates do not establish a measurement window; document the export period separately.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Normalized CSV export")
    parser.add_argument("--output", help="Optional JSON file path; otherwise print JSON")
    args = parser.parse_args()
    try:
        result = analyze(read_records(args.input))
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
        print(f"Saved report to {args.output}")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
