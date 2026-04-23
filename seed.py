"""
Run after each Render deployment to restore sample expenses:
  python seed.py
"""

import json
import uuid
import urllib.request
import urllib.error

API = "https://expense-tracker-le2w.onrender.com"

EXPENSES = [
    {"amount": "1200.00", "category": "Bills",     "description": "Rent — April",        "date": "2026-04-01"},
    {"amount": "85.50",   "category": "Food",      "description": "Groceries",            "date": "2026-04-03"},
    {"amount": "320.00",  "category": "Transport", "description": "Monthly metro pass",   "date": "2026-04-05"},
    {"amount": "450.00",  "category": "Bills",     "description": "Electricity bill",     "date": "2026-04-07"},
    {"amount": "120.50",  "category": "Food",      "description": "Lunch with team",      "date": "2026-04-10"},
    {"amount": "999.00",  "category": "Shopping",  "description": "Shoes",               "date": "2026-04-12"},
    {"amount": "60.00",   "category": "Health",    "description": "Pharmacy",             "date": "2026-04-14"},
    {"amount": "45.00",   "category": "Food",      "description": "Dinner",               "date": "2026-04-16"},
    {"amount": "85.00",   "category": "Food",      "description": "Groceries",            "date": "2026-04-18"},
    {"amount": "200.00",  "category": "Health",    "description": "Doctor visit",         "date": "2026-04-20"},
    {"amount": "75.00",   "category": "Transport", "description": "Cab to airport",       "date": "2026-04-21"},
    {"amount": "550.00",  "category": "Shopping",  "description": "Books and stationery", "date": "2026-04-22"},
]


def post(expense):
    body = json.dumps(expense).encode()
    req = urllib.request.Request(
        f"{API}/expenses",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Idempotency-Key": str(uuid.uuid4()),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            print(f"  ✓ [{data['id']:>2}] {expense['date']}  {expense['category']:<12} ₹{expense['amount']}")
    except urllib.error.HTTPError as e:
        err = json.loads(e.read())
        print(f"  ✗ {expense['date']} {expense['category']} — {err.get('detail', e.code)}")


print(f"Seeding {len(EXPENSES)} expenses → {API}\n")
for exp in EXPENSES:
    post(exp)
print("\nDone.")
