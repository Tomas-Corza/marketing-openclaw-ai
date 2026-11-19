"""Offline synthetic finance workflows for an interview demonstration.

No QuickBooks, Salesforce, banking, payroll or other production integration.
No writes to accounting systems. All amounts in USD and illustrative.
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict

def money(value):
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def seed_data(today=None):
    today = today or date.today()
    def d(offset): return (today + timedelta(days=offset)).isoformat()
    return {
        "jobs": [
            {"job_id": "JOB-1042", "customer": "Oakridge Home", "contract": 18400, "stage": "Installation"},
            {"job_id": "JOB-1043", "customer": "Cedar Homes", "contract": 9200, "stage": "Complete"},
            {"job_id": "JOB-1044", "customer": "Maple Property", "contract": 15200, "stage": "Service"},
        ],
        "purchase_orders": [
            {"po_id": "PO-7001", "vendor": "Pacific Glass Supply", "job_id": "JOB-1042", "amount": 4250},
            {"po_id": "PO-7002", "vendor": "Westside Hardware", "job_id": "JOB-1043", "amount": 1180},
            {"po_id": "PO-7003", "vendor": "Valley Freight", "job_id": "JOB-1044", "amount": 640},
        ],
        "payables": [
            {"invoice_id": "INV-9001", "vendor": "Pacific Glass Supply", "po_id": "PO-7001", "amount": 4250, "due": d(9), "status": "Open"},
            {"invoice_id": "INV-9002", "vendor": "Westside Hardware", "po_id": "PO-7002", "amount": 1200, "due": d(-5), "status": "Open"},
            {"invoice_id": "INV-9003", "vendor": "Valley Freight", "po_id": "PO-7003", "amount": 640, "due": d(12), "status": "Open"},
            {"invoice_id": "INV-9003", "vendor": "Valley Freight", "po_id": "PO-7003", "amount": 640, "due": d(12), "status": "Open"},
            {"invoice_id": "INV-9004", "vendor": "Unknown Contractor", "po_id": "PO-9999", "amount": 870, "due": d(4), "status": "Open"},
        ],
        "receivables": [
            {"invoice_id": "AR-3001", "customer": "Oakridge Home", "job_id": "JOB-1042", "billed": 9200, "paid": 4000, "due": d(-37)},
            {"invoice_id": "AR-3002", "customer": "Cedar Homes", "job_id": "JOB-1043", "billed": 9200, "paid": 9200, "due": d(-4)},
            {"invoice_id": "AR-3003", "customer": "Maple Property", "job_id": "JOB-1044", "billed": 7500, "paid": 0, "due": d(10)},
            {"invoice_id": "AR-3004", "customer": "Oakridge Home", "job_id": "JOB-1042", "billed": 9200, "paid": 0, "due": d(-8)},
        ],
        "ledger": [
            {"entry_id": "LED-01", "reference": "PAY-102", "amount": -4250, "account": "Checking"},
            {"entry_id": "LED-02", "reference": "PAY-103", "amount": -1180, "account": "Checking"},
            {"entry_id": "LED-03", "reference": "DEP-201", "amount": 4000, "account": "Checking"},
            {"entry_id": "LED-04", "reference": "DEP-202", "amount": 9200, "account": "Checking"},
        ],
        "bank": [
            {"bank_id": "BNK-01", "reference": "PAY-102", "amount": -4250, "account": "Checking"},
            {"bank_id": "BNK-02", "reference": "PAY-103", "amount": -1200, "account": "Checking"},
            {"bank_id": "BNK-03", "reference": "DEP-201", "amount": 4000, "account": "Checking"},
            {"bank_id": "BNK-04", "reference": "DEP-202", "amount": 9200, "account": "Checking"},
            {"bank_id": "BNK-05", "reference": "FEE-003", "amount": -35, "account": "Checking"},
        ],
        "timesheets": [
            {"employee": "Tech A", "job_id": "JOB-1042", "hours": 42, "rate": 28, "approved_hours": 40},
            {"employee": "Tech B", "job_id": "JOB-1043", "hours": 36, "rate": 30, "approved_hours": 36},
            {"employee": "Tech C", "job_id": "JOB-1044", "hours": 39, "rate": 27, "approved_hours": 39},
        ],
        "integrations": [
            {"system": "QuickBooks Online", "purpose": "Invoices, bills, payments, chart of accounts", "connection": "Not connected", "mode": "Proposed OAuth + read-only validation"},
            {"system": "Salesforce / CRM", "purpose": "Jobs, customers, purchase orders", "connection": "Not connected", "mode": "Proposed API + ID mapping"},
            {"system": "Bank feed", "purpose": "Transaction matching", "connection": "Not connected", "mode": "Proposed authorized feed or CSV"},
            {"system": "Time tracking / payroll", "purpose": "Approved hours and payroll exceptions", "connection": "Not connected", "mode": "Proposed approved export/API"},
            {"system": "Webhooks / n8n / Make", "purpose": "Events and review notifications", "connection": "Not connected", "mode": "Proposed integration"},
        ],
    }

def analyze(data, today=None):
    """Return deterministic suggested review actions; never post or approve money movements."""
    today = today or date.today()
    flags, audit = [], []
    def add(area, item, severity, reason, recommendation):
        row={"area":area,"record":item,"severity":severity,"reason":reason,"recommended_action":recommendation,"approval":"Human review required"}
        flags.append(row)
        audit.append({"stage":area,"record":item,"decision":"FLAG", "detail":reason})
    po = {r["po_id"]: r for r in data["purchase_orders"]}
    seen=set()
    ap_total=Decimal("0")
    for p in data["payables"]:
        key=(p["vendor"],p["invoice_id"])
        pid=p["invoice_id"]
        if key in seen:
            add("Accounts Payable",pid,"High","Duplicate vendor/invoice identifier","Hold invoice; investigate duplicate")
            continue
        seen.add(key)
        ap_total += money(p["amount"])
        match=po.get(p["po_id"])
        if not match:
            add("Invoice Matching",pid,"High","Purchase order not found","Request verified purchase order")
        elif match["vendor"]!=p["vendor"]:
            add("Invoice Matching",pid,"High","Vendor does not match purchase order","Validate vendor identity")
        elif money(match["amount"])!=money(p["amount"]):
            add("Invoice Matching",pid,"Medium",f"PO amount ${money(match['amount'])} vs invoice ${money(p['amount'])}","Review variance before approval")
        else:
            audit.append({"stage":"Invoice Matching","record":pid,"decision":"MATCH","detail":"Vendor, PO ID, and amount match"})
    ar_total=Decimal("0")
    aging=defaultdict(lambda:Decimal("0"))
    jobs={j["job_id"] for j in data["jobs"]}
    for r in data["receivables"]:
        balance=money(r["billed"])-money(r["paid"])
        if balance<0:
            add("Accounts Receivable",r["invoice_id"],"High","Payment exceeds invoice","Check credit or misapplied payment")
            continue
        ar_total+=balance
        overdue=(today-date.fromisoformat(r["due"])).days
        bucket="Current" if overdue<=0 else ("1–30" if overdue<=30 else ("31–60" if overdue<=60 else ("61–90" if overdue<=90 else "90+")))
        aging[bucket]+=balance
        if balance>0 and overdue>30:
            add("Accounts Receivable",r["invoice_id"],"Medium",f"Outstanding ${balance}; {overdue} days overdue","Prepare collections follow-up draft")
        if r["job_id"] not in jobs:
            add("CRM / AR",r["invoice_id"],"High","CRM job reference missing","Resolve job-to-invoice linkage")
    ledgers=defaultdict(list)
    for r in data["ledger"]:
        ledgers[(r["account"],r["reference"])].append(r)
    matched=set()
    for b in data["bank"]:
        key=(b["account"],b["reference"])
        candidates=ledgers.get(key,[])
        if len(candidates)!=1:
            add("Reconciliation",b["bank_id"],"Medium","Missing or ambiguous ledger match","Investigate transaction; no auto-posting")
        elif money(candidates[0]["amount"])!=money(b["amount"]):
            add("Reconciliation",b["bank_id"],"High",f"Bank ${money(b['amount'])} vs ledger ${money(candidates[0]['amount'])}","Investigate amount variance")
            matched.add(candidates[0]["entry_id"])
        else:
            matched.add(candidates[0]["entry_id"])
            audit.append({"stage":"Reconciliation","record":b["bank_id"],"decision":"MATCH","detail":"Account, reference and amount match"})
    for r in data["ledger"]:
        if r["entry_id"] not in matched:
            add("Reconciliation",r["entry_id"],"Medium","Ledger transaction has no matching bank transaction","Review outstanding ledger entry")
    payroll=Decimal("0")
    for t in data["timesheets"]:
        payroll+=money(t["hours"])*money(t["rate"])
        if t["hours"]>t["approved_hours"]:
            add("Payroll / Time",t["employee"],"High",f"{t['hours']} entered hours exceed {t['approved_hours']} approved","Send for supervisor approval; do not export payroll")
        if t["job_id"] not in jobs:
            add("Payroll / Time",t["employee"],"Medium","Unknown job ID","Verify job allocation")
    summary={"ar_outstanding":float(ar_total),"ap_open_unique":float(ap_total),"payroll_gross_illustrative":float(payroll),"exception_count":len(flags),"high_severity":sum(f["severity"]=="High" for f in flags),"aging":{k:float(aging[k]) for k in ["Current","1–30","31–60","61–90","90+"]}}
    return {"summary":summary,"exceptions":flags,"audit":audit}

def suggest_actions(result):
    """Rules-based agent-style proposed work queue, not LLM reasoning."""
    return [{"priority":e["severity"],"task":e["recommended_action"],"why":e["reason"],"source":e["record"],"category":e["area"],"execution":"Review only; no financial writes"} for e in result["exceptions"]]
