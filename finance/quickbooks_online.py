"""QuickBooks Online payroll-preparation adapter (read-only).

Uses the QBO Accounting API for permitted Employee and TimeActivity reads.
It does NOT run payroll, calculate compliant wages, or initiate direct deposits.
Tokens must be obtained via a separately implemented, secure OAuth flow.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from decimal import Decimal
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from finance.timekeeping import analyze_shifts

QBO_HOSTS = {"sandbox": "https://sandbox-quickbooks.api.intuit.com",
             "production": "https://quickbooks.api.intuit.com"}
REALM_PATTERN = re.compile(r"^[0-9]{1,30}$")


class QBOAccessError(RuntimeError):
    pass


class QBOReadOnlyClient:
    """A deliberately read-only QBO data client.

    OAuth access tokens are supplied by a trusted backend. No token persistence,
    payroll writes, or generic arbitrary-query method is exposed.
    """
    def __init__(self, realm_id, access_token, environment="sandbox"):
        if environment not in QBO_HOSTS:
            raise ValueError("environment must be sandbox or production")
        if not REALM_PATTERN.fullmatch(str(realm_id)):
            raise ValueError("Invalid QuickBooks company realm ID")
        if not access_token:
            raise ValueError("A separately authorized OAuth access token is required")
        self.realm_id = str(realm_id)
        self._access_token = access_token
        self.host = QBO_HOSTS[environment]

    def _query(self, entity, start=1, count=100):
        if entity not in {"Employee", "TimeActivity"}:
            raise ValueError("Only read-only Employee and TimeActivity queries are permitted")
        if not isinstance(start, int) or start < 1 or not isinstance(count, int) or not 1 <= count <= 1000:
            raise ValueError("Invalid pagination")
        import urllib.parse
        q = f"SELECT * FROM {entity} STARTPOSITION {start} MAXRESULTS {count}"
        url = f"{self.host}/v3/company/{self.realm_id}/query?"+urllib.parse.urlencode({"query": q, "minorversion": 75})
        request = Request(url, headers={"Authorization": f"Bearer {self._access_token}",
                                        "Accept": "application/json"}, method="GET")
        try:
            with urlopen(request, timeout=30) as response:
                data = json.load(response)
        except HTTPError as exc:
            raise QBOAccessError(f"QuickBooks query failed: HTTP {exc.code}") from None
        return data.get("QueryResponse", {}).get(entity, [])

    def employees(self, max_records=1000):
        return self._all("Employee", max_records)

    def time_activities(self, max_records=1000):
        return self._all("TimeActivity", max_records)

    def _all(self, entity, max_records):
        if not isinstance(max_records, int) or max_records < 1 or max_records > 10000:
            raise ValueError("max_records must be between 1 and 10000")
        rows = []
        while len(rows) < max_records:
            batch = self._query(entity, len(rows) + 1, min(100, max_records - len(rows)))
            rows.extend(batch)
            if not batch or len(batch) < 100:
                break
        return rows


def summarize_qbo_time_activities(activities):
    """Group QBO duration records for audit, without inferring payroll approval.

    QBO TimeActivity does not prove presence of raw clock punches or payroll
    approval; this function is purposefully a summary, not a compliance check.
    """
    totals = defaultdict(lambda: Decimal("0"))
    exceptions = []
    seen = set()
    for a in activities:
        activity_id = str(a.get("Id", "")).strip()
        employee_ref = a.get("EmployeeRef") or {}
        employee_id = str(employee_ref.get("value", "")).strip()
        day = str(a.get("TxnDate", ""))
        if not activity_id or activity_id in seen:
            exceptions.append({"record": activity_id, "reason": "Missing or duplicate TimeActivity ID"})
            continue
        seen.add(activity_id)
        if not employee_id or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
            exceptions.append({"record": activity_id, "reason": "Missing employee reference or date"})
            continue
        hours, minutes = a.get("Hours", 0), a.get("Minutes", 0)
        try:
            h, m = Decimal(str(hours)), Decimal(str(minutes))
            if not h.is_finite() or not m.is_finite() or h < 0 or m < 0 or m >= 60:
                raise ValueError()
        except (ValueError, TypeError, __import__("decimal").InvalidOperation):
            exceptions.append({"record": activity_id, "reason": "Invalid duration"})
            continue
        totals[(employee_id, day)] += h + m / Decimal(60)
    return {
        "daily_hours": [
            {"employee_id": employee_id, "date": day,
             "recorded_hours": str(total.quantize(Decimal("0.0001"))),
             "payroll_approved": False}
            for (employee_id, day), total in sorted(totals.items())
        ],
        "exceptions": exceptions,
        "note": "TimeActivity summary only; does not represent verified punches or approved payroll."
    }


def prepare_payroll_review(shifts, valid_job_ids, pay_period_start, pay_period_end):
    """Review complete shift-level records in an explicit inclusive pay period.

    All flags are retained. No payroll calculations or submissions occur.
    """
    from datetime import date
    start = date.fromisoformat(pay_period_start)
    end = date.fromisoformat(pay_period_end)
    if start > end:
        raise ValueError("Pay period end must not precede start")
    result = analyze_shifts(shifts, valid_job_ids)
    in_period = []
    outside = []
    for row in result["payroll_ready"]:
        day = date.fromisoformat(row["work_date"])
        if start <= day <= end:
            in_period.append(row)
        else:
            outside.append(row["shift_id"])
    return {
        "period": {"start": pay_period_start, "end": pay_period_end},
        "approved_hours_for_review": in_period,
        "exceptions": result["exceptions"],
        "out_of_period_shift_ids": outside,
        "status": "REVIEW_ONLY_NOT_SUBMITTED",
        "requires_payroll_manager_approval": True,
        "warning": "Hours are not wage calculations. Verify overtime, paid breaks, leave, pay types and pay-period boundaries in QuickBooks."
    }
