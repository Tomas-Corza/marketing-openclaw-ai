"""Synthetic, deterministic timekeeping controls for review-first finance workflows.

All records are fictional. No employee tracking, payroll calculations, or writes
to time, accounting, or payroll vendors are performed.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

ZONE = "America/Los_Angeles"
MAX_SHIFT_HOURS = Decimal("16")
MAX_DAILY_HOURS = Decimal("12")


def demo_shifts():
    """Fictional shifts with intentional exceptions to make reviews inspectable."""
    return [
        {"shift_id": "SHIFT-001", "employee_id": "EMP-101", "job_id": "JOB-1042",
         "start": "2026-11-16T08:00:00-08:00", "end": "2026-11-16T16:30:00-08:00",
         "break_minutes": 30, "status": "approved", "approver": "Supervisor A"},
        {"shift_id": "SHIFT-002", "employee_id": "EMP-102", "job_id": "JOB-1043",
         "start": "2026-11-16T08:00:00-08:00", "end": "2026-11-16T17:00:00-08:00",
         "break_minutes": 0, "status": "pending", "approver": ""},
        {"shift_id": "SHIFT-003", "employee_id": "EMP-101", "job_id": "JOB-1044",
         "start": "2026-11-16T15:30:00-08:00", "end": "2026-11-16T19:00:00-08:00",
         "break_minutes": 30, "status": "approved", "approver": "Supervisor A"},
        {"shift_id": "SHIFT-004", "employee_id": "EMP-103", "job_id": "JOB-9999",
         "start": "2026-11-17T08:00:00-08:00", "end": None,
         "break_minutes": 30, "status": "pending", "approver": ""},
        {"shift_id": "SHIFT-005", "employee_id": "EMP-104", "job_id": "JOB-1042",
         "start": "2026-11-17T08:00:00-08:00", "end": "2026-11-17T16:30:00-08:00",
         "break_minutes": 30, "status": "approved", "approver": "Supervisor B"},
    ]


def _time(value):
    if not value:
        raise ValueError("missing timestamp")
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must include UTC offset")
    return parsed.astimezone(timezone.utc)


def _decimal(value):
    try:
        number = Decimal(str(value))
        if not number.is_finite():
            raise ValueError("non-finite break")
        return number
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("invalid break duration") from exc


def analyze_shifts(shifts, valid_job_ids=None, timezone_name=ZONE):
    """Flag exceptions and prepare only individually clear, approved hours.

    Payroll-ready means structurally reviewed hours, NOT a payroll calculation or
    a compliance certification. An exception blocks its shift from export.
    """
    tz = ZoneInfo(timezone_name)
    jobs = None if valid_job_ids is None else set(valid_job_ids)
    rows, exceptions, audit, parsed = [], [], [], {}
    id_counts = Counter(str(s.get("shift_id", "")).strip() for s in shifts)
    issues_by_index = defaultdict(list)

    def flag(index, rule, detail, severity="High"):
        shift = shifts[index]
        row = {"shift_id": shift.get("shift_id", ""), "employee_id": shift.get("employee_id", ""),
               "rule": rule, "severity": severity, "detail": detail,
               "resolution": "Human review required", "source": "deterministic_rule"}
        exceptions.append(row)
        issues_by_index[index].append(rule)
        audit.append({"shift_id": row["shift_id"], "event": "FLAG", "rule": rule, "detail": detail})

    for i, shift in enumerate(shifts):
        sid = str(shift.get("shift_id", "")).strip()
        employee = str(shift.get("employee_id", "")).strip()
        job = str(shift.get("job_id", "")).strip()
        if not sid or id_counts[sid] > 1:
            flag(i, "duplicate_or_missing_id", "Shift identifier is empty or duplicated")
        if not employee:
            flag(i, "missing_employee", "Employee ID is required")
        if not job or (jobs is not None and job not in jobs):
            flag(i, "unknown_job", "Job ID is missing or does not match the CRM job list")
        status = str(shift.get("status", "")).lower().strip()
        if status != "approved" or not str(shift.get("approver", "")).strip():
            flag(i, "approval_required", "Approved status and named approver are both required")
        try:
            start, end = _time(shift.get("start")), _time(shift.get("end"))
            duration = Decimal(str((end - start).total_seconds())) / Decimal("3600")
            if duration <= 0:
                raise ValueError("end must follow start")
            parsed[i] = (start, end, employee)
            breaks = _decimal(shift.get("break_minutes"))
            if breaks < 0 or breaks > duration * 60:
                raise ValueError("break exceeds shift or is negative")
            payable = duration - breaks / 60
            if duration > MAX_SHIFT_HOURS:
                flag(i, "long_shift", "Recorded shift exceeds 16 elapsed hours")
            if duration >= 6 and breaks == 0:
                flag(i, "missing_break", "No break recorded for a shift of at least six hours; review applicable policy", "Medium")
            local_day = start.astimezone(tz).date().isoformat()
            rows.append({"shift_id": sid, "employee_id": employee, "job_id": job,
                         "work_date": local_day, "hours": round(float(payable), 4),
                         "status": status, "approver": shift.get("approver", "")})
        except (ValueError, OverflowError) as exc:
            flag(i, "invalid_shift", str(exc))
            rows.append({"shift_id": sid, "employee_id": employee, "job_id": job,
                         "work_date": "", "hours": None, "status": status,
                         "approver": shift.get("approver", "")})

    # Compare in UTC to handle offset transitions reliably.
    by_employee = defaultdict(list)
    by_day = defaultdict(list)
    for i, (start, end, employee) in parsed.items():
        if employee:
            by_employee[employee].append((start, end, i))
        if rows[i]["hours"] is not None:
            by_day[(employee, rows[i]["work_date"])].append(i)
    for intervals in by_employee.values():
        intervals.sort()
        for j, (start, end, i) in enumerate(intervals):
            for prior_start, prior_end, prior_i in intervals[:j]:
                if start < prior_end and end > prior_start:
                    flag(i, "overlapping_shift", f"Overlaps shift {shifts[prior_i].get('shift_id')}")
                    flag(prior_i, "overlapping_shift", f"Overlaps shift {shifts[i].get('shift_id')}")
    for (employee, day), indices in by_day.items():
        total = sum(Decimal(str(rows[i]["hours"])) for i in indices)
        if total > MAX_DAILY_HOURS:
            for i in indices:
                flag(i, "high_daily_hours", f"{employee} recorded {total} hours on {day}; review overtime and shift dates", "Medium")

    export = []
    for i, row in enumerate(rows):
        if issues_by_index[i]:
            audit.append({"shift_id": row["shift_id"], "event": "HELD",
                          "rule": ",".join(sorted(set(issues_by_index[i]))), "detail": "Excluded from export"})
        else:
            export.append({"shift_id": row["shift_id"], "employee_id": row["employee_id"],
                           "job_id": row["job_id"], "work_date": row["work_date"],
                           "approved_hours": row["hours"], "approved_by": row["approver"]})
            audit.append({"shift_id": row["shift_id"], "event": "READY",
                          "rule": "verified_hours", "detail": "Hours available for human-controlled export"})
    return {"shifts": rows, "exceptions": exceptions, "audit": audit,
            "payroll_ready": export,
            "summary": {"shift_count": len(shifts), "flagged_shifts": len(issues_by_index),
                        "ready_shifts": len(export),
                        "approved_hours_ready": round(sum(x["approved_hours"] for x in export), 4)}}
