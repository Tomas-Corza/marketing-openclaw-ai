"""Dedicated synthetic accounting automation dashboard.

Run: streamlit run finance/dashboard.py
"""
from pathlib import Path
import sys
import json
import csv
import io
import streamlit as st
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from finance.engine import seed_data, analyze, suggest_actions
from finance.timekeeping import analyze_shifts, demo_shifts

def make_hours_csv(rows):
    buffer = io.StringIO()
    columns = ["shift_id", "employee_id", "job_id", "work_date", "approved_hours", "approved_by"]
    writer = csv.DictWriter(buffer, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()

st.set_page_config(page_title="OpenClaw | Finance Operations", page_icon="🧾", layout="wide")
st.title("Finance Automation Control Center")
st.caption("Marketing OpenClaw AI · Accounting workflow prototype")
st.warning("SYNTHETIC DEMO ONLY · No bank, QuickBooks, Salesforce, payroll, or AI model connection. Rule-based workflows; no financial writes.")
if "finance_data" not in st.session_state:
    st.session_state.finance_data=seed_data()
if "timekeeping_shifts" not in st.session_state:
    st.session_state.timekeeping_shifts = demo_shifts()
if "finance_run" not in st.session_state:
    st.session_state.finance_run=False

with st.sidebar:
    st.header("Automation controls")
    st.write("Mode: offline synthetic data")
    if st.button("▶ Run finance validation",type="primary",width="stretch"):
        st.session_state.finance_run=True
    if st.button("Reset synthetic dataset",width="stretch"):
        st.session_state.finance_data=seed_data()
        st.session_state.timekeeping_shifts=demo_shifts()
        st.session_state.finance_run=False
    st.divider()
    st.markdown("**Safety controls**")
    st.caption("No approval, payment, payroll submission, bank update, or QuickBooks write action is implemented.")
    st.caption("Future connectors require authenticated, authorized deployment.")

data=st.session_state.finance_data
result=analyze(data)
summary=result["summary"]
a,b,c,d,e=st.columns(5)
a.metric("AR outstanding",f"${summary['ar_outstanding']:,.2f}")
b.metric("AP outstanding¹",f"${summary['ap_open_unique']:,.2f}")
c.metric("Illustrative payroll",f"${summary['payroll_gross_illustrative']:,.2f}")
d.metric("Exceptions",summary["exception_count"])
e.metric("High priority",summary["high_severity"])
st.caption("¹ AP excludes duplicate vendor/invoice IDs from the total. Figures are fictional and not accounting statements.")
tabs=st.tabs(["Overview","Accounts Receivable","Accounts Payable","Invoice Matching","Bank Reconciliation","Payroll & Time","Timekeeping Review","CRM / Jobs","Exceptions & Agent Queue","Integrations","Audit Log"])
with tabs[0]:
    st.subheader("Finance operations snapshot")
    left,right=st.columns(2)
    with left:
        st.markdown("**AR aging**")
        st.bar_chart(summary["aging"])
    with right:
        st.markdown("**Exception distribution**")
        counts={}
        for issue in result["exceptions"]:
            counts[issue["area"]]=counts.get(issue["area"],0)+1
        st.bar_chart(counts)
    st.info("Workflow: synthetic inputs → deterministic matching/validation → exception queue → human approval. Future authenticated APIs could replace the inputs.")
with tabs[1]:
    st.subheader("Customer invoicing, collections and aging")
    st.dataframe(data["receivables"],width="stretch",hide_index=True)
    st.markdown("**Aging summary (open balances)**")
    st.dataframe([{"bucket":k,"balance_usd":v} for k,v in summary["aging"].items()],hide_index=True,width="stretch")
with tabs[2]:
    st.subheader("Vendor bills and payment review")
    st.dataframe(data["payables"],width="stretch",hide_index=True)
    st.caption("Vendor payments are not initiated or approved.")
with tabs[3]:
    st.subheader("Invoice verification against purchase orders")
    st.dataframe(data["purchase_orders"],hide_index=True,width="stretch")
    st.dataframe([x for x in result["exceptions"] if x["area"] in ("Invoice Matching","Accounts Payable")],hide_index=True,width="stretch")
with tabs[4]:
    st.subheader("Bank ↔ ledger reconciliation")
    left,right=st.columns(2)
    with left:
        st.markdown("**Bank feed**")
        st.dataframe(data["bank"],hide_index=True,width="stretch")
    with right:
        st.markdown("**Accounting ledger**")
        st.dataframe(data["ledger"],hide_index=True,width="stretch")
    st.dataframe([x for x in result["exceptions"] if x["area"]=="Reconciliation"],hide_index=True,width="stretch")
with tabs[5]:
    st.subheader("Hours, approval exceptions and estimated gross pay")
    st.dataframe(data["timesheets"],hide_index=True,width="stretch")
    st.dataframe([x for x in result["exceptions"] if x["area"]=="Payroll / Time"],hide_index=True,width="stretch")
    st.caption("Straight-time estimation only. Not a payroll calculator; excludes overtime rules, withholding, taxes and benefits.")
with tabs[6]:
    st.subheader("Timekeeping exception review and payroll preparation")
    st.caption("Fictional shift data only. Deterministic validation, not real-time attendance monitoring or payroll processing.")
    st.dataframe(st.session_state.timekeeping_shifts, hide_index=True, width="stretch")
    time_results = analyze_shifts(
        st.session_state.timekeeping_shifts,
        {j["job_id"] for j in data["jobs"]},
    )
    k1, k2, k3 = st.columns(3)
    k1.metric("Recorded shifts", time_results["summary"]["shift_count"])
    k2.metric("Held shifts", time_results["summary"]["flagged_shifts"])
    k3.metric("Approved hours ready", time_results["summary"]["approved_hours_ready"])
    st.markdown("**Exceptions requiring human review**")
    if time_results["exceptions"]:
        st.dataframe(time_results["exceptions"], hide_index=True, width="stretch")
    else:
        st.success("No deterministic exceptions identified in this dataset.")
    st.markdown("**Review-only payroll hours export**")
    st.dataframe(time_results["payroll_ready"], hide_index=True, width="stretch")
    st.download_button(
        "Download reviewed hours (CSV)",
        data=make_hours_csv(time_results["payroll_ready"]),
        file_name="synthetic-approved-hours-review.csv", mime="text/csv",
        disabled=not bool(time_results["payroll_ready"]),
    )
    with st.expander("Timekeeping audit decisions"):
        st.dataframe(time_results["audit"], hide_index=True, width="stretch")
    st.warning("No overtime, meal/rest compliance, wages, deductions, taxes, or payroll submission calculated. Export requires further payroll-team verification.")
with tabs[7]:
    st.subheader("CRM job matching")
    st.dataframe(data["jobs"],hide_index=True,width="stretch")
    st.caption("Job IDs are fictional and demonstrate proposed CRM-to-finance mapping.")
with tabs[8]:
    st.subheader("Exception monitoring")
    st.dataframe(result["exceptions"],hide_index=True,width="stretch")
    st.markdown("**Proposed agent work queue (rules-based)**")
    if st.session_state.finance_run:
        st.dataframe(suggest_actions(result),hide_index=True,width="stretch")
        st.success("Validation run complete; proposed tasks are review-only.")
    else:
        st.info("Click 'Run finance validation' in the sidebar to generate the proposed work queue.")
with tabs[9]:
    st.subheader("Integration readiness")
    st.dataframe(data["integrations"],hide_index=True,width="stretch")
    st.warning("All connectors are proposed, not implemented. No API keys or OAuth tokens are requested or stored.")
    st.markdown("**Production rollout:** OAuth/read-only discovery → data mapping → idempotent matching → audit logs → supervisor approval → narrowly scoped writes → retries, monitoring and rollback.")
with tabs[10]:
    st.subheader("Deterministic rule audit trail")
    st.dataframe(result["audit"],hide_index=True,width="stretch")
    st.download_button("Download audit + exception JSON",data=json.dumps(result,indent=2),file_name="synthetic-finance-audit.json",mime="application/json")
