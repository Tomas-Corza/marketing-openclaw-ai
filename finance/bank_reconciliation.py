"""Deterministic, conservative bank-to-ledger reconciliation suggestions.

Never marks accounts reconciled or posts entries. Plaid amount direction is
positive for debit/outflow, negative for credit/inflow; ledger direction is
positive for inflow and negative for outflow.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def amount(value):
    try:
        d = Decimal(str(value))
        if not d.is_finite():
            raise ValueError("Non-finite amount")
        return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("Invalid transaction amount") from exc


def reconcile(bank_transactions, ledger_entries, account_mapping):
    """Return suggestions with linked source IDs; ambiguous matches are held.

    account_mapping maps Plaid account_id -> ledger account identifier.
    Only posted, valid dated transactions with a unique exact amount and
    matching ledger account and ISO date qualify for suggested match.
    """
    matched, flags, audit = [], [], []
    bank_by_key, ledger_by_key = defaultdict(list), defaultdict(list)
    bank_ids = Counter(str(b.get("transaction_id", "")) for b in bank_transactions)
    ledger_ids = Counter(str(l.get("entry_id", "")) for l in ledger_entries)
    def hold(kind, record_id, reason):
        flags.append({"area": "Bank Reconciliation", "source": kind,
                      "record": record_id, "reason": reason,
                      "resolution": "Human review required"})
        audit.append({"source": kind, "record": record_id, "decision": "HOLD", "detail": reason})

    for b in bank_transactions:
        txid = str(b.get("transaction_id", ""))
        if not txid or bank_ids[txid] > 1:
            hold("bank", txid, "Missing or duplicate transaction ID")
            continue
        if b.get("pending", False):
            hold("bank", txid, "Pending bank transaction; wait for posted record")
            continue
        account = account_mapping.get(b.get("account_id"))
        if not account:
            hold("bank", txid, "Unmapped bank account")
            continue
        try:
            day = date.fromisoformat(str(b["date"]))
            # Invert Plaid's sign to match standard ledger conventions.
            value = -amount(b["amount"])
        except (KeyError, ValueError, TypeError):
            hold("bank", txid, "Missing or invalid bank date or amount")
            continue
        bank_by_key[(account, day, value)].append(b)
    for l in ledger_entries:
        entry = str(l.get("entry_id", ""))
        if not entry or ledger_ids[entry] > 1:
            hold("ledger", entry, "Missing or duplicate ledger entry ID")
            continue
        try:
            key = (str(l["account"]), date.fromisoformat(str(l["date"])), amount(l["amount"]))
            if not key[0]:
                raise ValueError("Missing account")
        except (KeyError, ValueError, TypeError):
            hold("ledger", entry, "Missing or invalid ledger account, date or amount")
            continue
        ledger_by_key[key].append(l)
    for key in set(bank_by_key) | set(ledger_by_key):
        banks, ledgers = bank_by_key[key], ledger_by_key[key]
        if len(banks) == 1 and len(ledgers) == 1:
            b, l = banks[0], ledgers[0]
            matched.append({"bank_transaction_id": b["transaction_id"],
                            "ledger_entry_id": l["entry_id"], "account": key[0],
                            "date": key[1].isoformat(), "amount": str(key[2]),
                            "decision": "PROPOSED_MATCH", "requires_approval": True})
            audit.append({"source": "bank+ledger",
                          "record": f"{b['transaction_id']} / {l['entry_id']}",
                          "decision": "PROPOSED_MATCH", "detail": "Unique account/date/amount match; human confirmation required"})
        else:
            reason = ("Ambiguous one-to-many or many-to-many candidates"
                      if banks and ledgers else "No counterpart found")
            for b in banks:
                hold("bank", b["transaction_id"], reason)
            for l in ledgers:
                hold("ledger", l["entry_id"], reason)
    return {"proposed_matches": sorted(matched, key=lambda r: r["bank_transaction_id"]),
            "exceptions": flags, "audit": audit,
            "summary": {"proposed_matches": len(matched), "exceptions": len(flags),
                        "source_bank_records": len(bank_transactions),
                        "source_ledger_records": len(ledger_entries)}}


def synthetic_example():
    bank = [
        {"transaction_id": "BANK-101", "account_id": "plaid-demo-checking", "date": "2026-11-16", "amount": 425.00, "pending": False},
        {"transaction_id": "BANK-102", "account_id": "plaid-demo-checking", "date": "2026-11-17", "amount": -1200.00, "pending": False},
        {"transaction_id": "BANK-103", "account_id": "plaid-demo-checking", "date": "2026-11-18", "amount": 39.00, "pending": True},
        {"transaction_id": "BANK-104", "account_id": "plaid-demo-checking", "date": "2026-11-18", "amount": 72.00, "pending": False},
    ]
    ledger = [
        {"entry_id": "LEDGER-101", "account": "Checking", "date": "2026-11-16", "amount": -425.00},
        {"entry_id": "LEDGER-102", "account": "Checking", "date": "2026-11-17", "amount": 1200.00},
        {"entry_id": "LEDGER-103", "account": "Checking", "date": "2026-11-18", "amount": -72.00},
        {"entry_id": "LEDGER-104", "account": "Checking", "date": "2026-11-18", "amount": -72.00},
    ]
    return bank, ledger, {"plaid-demo-checking": "Checking"}
