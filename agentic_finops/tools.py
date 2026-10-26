"""Tools the agent can call. Each is a plain, deterministic Python function."""
import re
import statistics
from datetime import datetime

from sample_data import APPROVED_VENDORS, VENDOR_HISTORY

AUTO_APPROVE_LIMIT = 5000.0

CATEGORY_KEYWORDS = {
    "Cloud & Software": ["cloud", "hosting", "software", "license"],
    "Office Supplies": ["paper", "stationery", "printer", "furniture"],
    "Travel": ["flight", "hotel", "taxi", "travel"],
    "Professional Services": ["consulting", "legal", "audit"],
    "Payroll": ["salary", "payroll"],
}

_seen_invoices: list[dict] = []   # simple in-memory state for duplicate checks


def extract_invoice(text: str) -> dict:
    """Parse raw invoice text into structured fields."""
    def grab(pattern):
        m = re.search(pattern, text, re.I)
        return m.group(1).strip() if m else None

    total = grab(r"Total:\s*\$?([\d,]+\.?\d*)")
    return {
        "invoice_no": grab(r"Invoice\s*#\s*([\w-]+)"),
        "vendor": grab(r"Vendor:\s*(.+)"),
        "date": grab(r"Date:\s*([\d-]+)"),
        "description": grab(r"Description:\s*(.+)"),
        "amount": float(total.replace(",", "")) if total else None,
    }


def categorize_expense(description: str) -> str:
    """Rule-based expense categorisation."""
    desc = (description or "").lower()
    for category, words in CATEGORY_KEYWORDS.items():
        if any(w in desc for w in words):
            return category
    return "Uncategorized"


def detect_anomalies(invoice: dict) -> list[str]:
    """Return a list of red flags for an invoice."""
    flags = []
    if invoice["vendor"] not in APPROVED_VENDORS:
        flags.append("UNAPPROVED_VENDOR")

    for prev in _seen_invoices:
        if prev["invoice_no"] == invoice["invoice_no"] or (
            prev["vendor"] == invoice["vendor"] and prev["amount"] == invoice["amount"]
            and prev["description"] == invoice["description"]
        ):
            flags.append(f"POSSIBLE_DUPLICATE_OF_{prev['invoice_no']}")
            break

    history = VENDOR_HISTORY.get(invoice["vendor"], [])
    if len(history) >= 3:
        mean, sd = statistics.mean(history), statistics.pstdev(history) or 1
        if (invoice["amount"] - mean) / sd > 3:
            flags.append(f"AMOUNT_OUTLIER (avg {mean:.0f})")

    _seen_invoices.append(invoice)
    return flags


def decide_payment(invoice: dict, flags: list[str]) -> dict:
    """Policy engine: approve, escalate to a human, or reject."""
    if any(f.startswith("POSSIBLE_DUPLICATE") for f in flags):
        return {"decision": "REJECT", "reason": "Duplicate invoice"}
    if flags:
        return {"decision": "ESCALATE", "reason": "Flags: " + ", ".join(flags)}
    if invoice["amount"] > AUTO_APPROVE_LIMIT:
        return {"decision": "ESCALATE", "reason": f"Amount above auto-approve limit {AUTO_APPROVE_LIMIT:.0f}"}
    return {"decision": "APPROVE", "reason": "Passed all checks"}


def reconcile(invoice: dict, bank_transactions: list[dict]) -> dict | None:
    """Match an invoice to a bank transaction by amount, vendor name and date."""
    inv_date = datetime.fromisoformat(invoice["date"])
    vendor_key = invoice["vendor"].split()[0].lower()
    for txn in bank_transactions:
        days = abs((datetime.fromisoformat(txn["date"]) - inv_date).days)
        if txn["amount"] == invoice["amount"] and vendor_key in txn["description"].lower() and days <= 10:
            return txn
    return None


TOOLS = {
    "extract_invoice": extract_invoice,
    "categorize_expense": categorize_expense,
    "detect_anomalies": detect_anomalies,
    "decide_payment": decide_payment,
    "reconcile": reconcile,
}
