"""
QuickBooks and email connectors.

Both are mocked for now. The mock data uses the same field names as the real
APIs (QBO Bill/Invoice objects, Gmail message fields) so agent.py won't need changes
when these are replaced with real calls.
"""
from datetime import date
_MOCK_INVOICES = [
    {
        "Id": "1042",
        "VendorRef": {"name": "Apex Office Supplies LLC"},
        "TotalAmt": 4788.00,
        "Balance": 4788.00,
        "DueDate": "2026-09-13",
        "Status": "Overdue",
    },
    {
        "Id": "1055",
        "VendorRef": {"name": "CloudHost Data Services"},
        "TotalAmt": 1323.00,
        "Balance": 0.00,
        "DueDate": "2026-09-16",
        "Status": "Paid",
    },
]


def get_overdue_invoices():
    today = date.today().isoformat()
    return [
        inv for inv in _MOCK_INVOICES
        if inv["Balance"] > 0 and inv["DueDate"] < today
    ] or [inv for inv in _MOCK_INVOICES if inv["Status"] == "Overdue"]


def get_invoice_by_id(invoice_id: str):
    for inv in _MOCK_INVOICES:
        if inv["Id"] == str(invoice_id):
            return inv
    return None


def get_cash_position_summary():
    total_outstanding = sum(inv["Balance"] for inv in _MOCK_INVOICES)
    return {
        "total_outstanding": total_outstanding,
        "invoice_count_outstanding": sum(1 for i in _MOCK_INVOICES if i["Balance"] > 0),
        "as_of": date.today().isoformat(),
    }

_MOCK_EMAILS = [
    {
        "from": "accounts@apexofficesupplies.com",
        "subject": "Payment reminder - Invoice #1042",
        "date": "2026-09-05",
        "snippet": "Friendly reminder that Invoice #1042 for $4,788.00 is due 2026-09-13.",
    },
    {
        "from": "finance@northwindconsulting.ae",
        "subject": "RE: Payment reminder - Invoice #1042",
        "date": "2026-09-06",
        "snippet": "Requesting extension to 2026-09-20 due to a temporary cash flow gap.",
    },
]


def search_emails(keyword: str):
    keyword_lower = keyword.lower()
    return [
        e for e in _MOCK_EMAILS
        if keyword_lower in e["subject"].lower() or keyword_lower in e["snippet"].lower()
    ]
