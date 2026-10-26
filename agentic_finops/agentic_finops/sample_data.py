"""Sample data: raw invoice texts, approved vendors, history and bank transactions."""

APPROVED_VENDORS = {"Acme Cloud Services", "OfficeMart", "TravelEase", "PayrollPro"}

INVOICE_TEXTS = [
    "Invoice #INV-1001\nVendor: Acme Cloud Services\nDate: 2026-10-01\nDescription: Monthly cloud hosting\nTotal: $1,200.00",
    "Invoice #INV-1002\nVendor: OfficeMart\nDate: 2026-10-03\nDescription: Printer paper and stationery\nTotal: $310.50",
    "Invoice #INV-1003\nVendor: TravelEase\nDate: 2026-10-05\nDescription: Flight tickets for sales team\nTotal: $2,450.00",
    "Invoice #INV-1001\nVendor: Acme Cloud Services\nDate: 2026-10-06\nDescription: Monthly cloud hosting\nTotal: $1,200.00",  # duplicate
    "Invoice #INV-1004\nVendor: QuickFixers Ltd\nDate: 2026-10-07\nDescription: Consulting services\nTotal: $4,800.00",       # unknown vendor
    "Invoice #INV-1005\nVendor: OfficeMart\nDate: 2026-10-09\nDescription: Office furniture\nTotal: $18,500.00",             # unusually large
]

# Past invoice amounts per vendor (used for anomaly detection)
VENDOR_HISTORY = {
    "Acme Cloud Services": [1150, 1200, 1180, 1210],
    "OfficeMart": [280, 300, 350, 295],
    "TravelEase": [2100, 2500, 2300],
}

BANK_TRANSACTIONS = [
    {"id": "TXN-9001", "date": "2026-10-02", "description": "ACME CLOUD SERVICES", "amount": 1200.00},
    {"id": "TXN-9002", "date": "2026-10-04", "description": "OFFICEMART PAYMENT", "amount": 310.50},
    {"id": "TXN-9003", "date": "2026-10-08", "description": "TRAVELEASE BOOKING", "amount": 2450.00},
]
