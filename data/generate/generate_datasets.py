#!/usr/bin/env python3
"""
DataQ — Sample Dataset Generator
=======================================
Fully reproducible (seed=42). Generates messy multi-source e-commerce data
with deliberate quality issues mapped to the Phase 0 quality rules.

Industry : E-commerce
Locale   : Kenyan-mixed (Kenyan + international names/phones)
Entities : ~200 canonical customers

Outputs
-------
data/samples/
    crm_customers.csv
    erp_customers.csv
    erp_transactions.csv
    marketing_customers.xlsx
data/ground_truth/
    ground_truth.csv
    injected_issues.json
    data_dictionary.md
"""

from __future__ import annotations

import json
import random
import string
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
from faker import Faker

from config import (
    SEED,
    N_CANONICAL_CUSTOMERS,
    N_ERP_TRANSACTIONS,
    CRM_COVERAGE,
    ERP_COVERAGE,
    MKT_COVERAGE,
    WITHIN_SOURCE_DUP_RATE,
    COMPLETENESS_RATE,
    VALIDITY_RATE,
    CONFLICT_RATE,
    ANOMALY_RATE,
    SAMPLES_DIR,
    GROUND_TRUTH_DIR,
)

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
random.seed(SEED)
Faker.seed(SEED)
fake = Faker()
fake_ke = Faker("en_US")  # base; we inject Kenyan flavour manually

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLES_PATH = PROJECT_ROOT / SAMPLES_DIR
GT_PATH = PROJECT_ROOT / GROUND_TRUTH_DIR
SAMPLES_PATH.mkdir(parents=True, exist_ok=True)
GT_PATH.mkdir(parents=True, exist_ok=True)

# Kenyan-flavoured name pools
KE_FIRST = [
    "Wanjiku", "Achieng", "Njeri", "Atieno", "Wambui", "Akinyi", "Nyokabi",
    "Kamau", "Otieno", "Ochieng", "Kipchoge", "Mwangi", "Kariuki", "Onyango",
    "Mutua", "Wekesa", "Njoroge", "Odhiambo", "Kiptoo", "Cheruiyot",
    "Faith", "Grace", "Mercy", "Joy", "Brian", "Kevin", "Dennis", "Collins",
]
KE_LAST = [
    "Wanjiru", "Otieno", "Kamau", "Ochieng", "Mwangi", "Njeri", "Kariuki",
    "Odhiambo", "Wekesa", "Mutua", "Kipchoge", "Cheruiyot", "Njoroge",
    "Onyango", "Achieng", "Atieno", "Nyokabi", "Kiptoo", "Wambui", "Kimani",
]

CURRENCIES = ["KES", "USD", "EUR"]
STATUSES = ["active", "inactive", "unknown"]
TX_STATUSES = ["completed", "pending", "refunded", "disputed"]
PRODUCTS = [
    "Wireless Earbuds", "Phone Case", "Laptop Stand", "USB-C Hub",
    "Smart Watch Band", "Power Bank 20000mAh", "Bluetooth Speaker",
    "Keyboard Cover", "Screen Protector", "Cable Organizer",
    "Annual Subscription", "Monthly Plan", "Gift Card 1000", "Express Shipping",
]

injected_issues: list[dict[str, Any]] = []


def log_issue(
    rule_id: str,
    entity_type: str,
    record_id: str,
    source: str,
    field: str,
    injected_value: Any,
    expected_or_note: str,
    severity: str = "High",
):
    injected_issues.append(
        {
            "rule_id": rule_id,
            "entity_type": entity_type,
            "record_id": record_id,
            "source": source,
            "field": field,
            "injected_value": str(injected_value) if injected_value is not None else None,
            "note": expected_or_note,
            "severity": severity,
        }
    )


def new_id(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex[:10]}"


def kenyan_phone(style: str = "normal") -> str:
    """Generate Kenyan mobile numbers in different formats."""
    base = f"7{random.randint(10000000, 99999999)}"
    if style == "e164":
        return f"+254{base}"
    if style == "local":
        return f"0{base}"
    if style == "spaced":
        return f"+254 {base[:3]} {base[3:6]} {base[6:]}"
    if style == "dashed":
        return f"0{base[:3]}-{base[3:6]}-{base[6:]}"
    if style == "messy":
        return f"254{base}"
    return f"+254{base}"


def make_name(kenyan_bias: float = 0.55) -> tuple[str, str, str]:
    if random.random() < kenyan_bias:
        first = random.choice(KE_FIRST)
        last = random.choice(KE_LAST)
    else:
        first = fake.first_name()
        last = fake.last_name()
    full = f"{first} {last}"
    return first, last, full


def random_dob(min_age: int = 18, max_age: int = 70) -> date:
    today = date.today()
    start = today - timedelta(days=max_age * 365)
    end = today - timedelta(days=min_age * 365)
    return fake.date_between(start_date=start, end_date=end)


def mess_email(email: str) -> str:
    """Introduce validity issues."""
    choice = random.choice(["missing_at", "double_dot", "trailing_space", "no_tld", "ok"])
    if choice == "missing_at":
        return email.replace("@", "")
    if choice == "double_dot":
        return email.replace(".", "..", 1)
    if choice == "trailing_space":
        return email + " "
    if choice == "no_tld":
        return email.split("@")[0] + "@mail"
    return email


# ---------------------------------------------------------------------------
# 1. Create canonical (ground-truth) customers
# ---------------------------------------------------------------------------
print("Creating canonical customers...")

canonical: list[dict] = []
for i in range(N_CANONICAL_CUSTOMERS):
    first, last, full = make_name()
    email = f"{first.lower()}.{last.lower()}{random.randint(1, 99)}@example.com"
    phone = kenyan_phone(random.choice(["e164", "local", "e164"]))
    dob = random_dob()
    city = random.choice(
        ["Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret", "Thika", "London", "New York", "Lagos"]
    )
    country = "KE" if city in ["Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret", "Thika"] else random.choice(["US", "GB", "NG", "KE"])
    status = random.choices(STATUSES, weights=[0.8, 0.15, 0.05])[0]

    canonical.append(
        {
            "true_id": f"cust_{i:04d}",
            "first_name": first,
            "last_name": last,
            "full_name": full,
            "email": email,
            "phone": phone,
            "date_of_birth": dob.isoformat(),
            "address_line1": fake.street_address(),
            "city": city,
            "country": country,
            "status": status,
        }
    )

canonical_df = pd.DataFrame(canonical)

# ---------------------------------------------------------------------------
# 2. Helper: copy a canonical record into a source with controlled mess
# ---------------------------------------------------------------------------
def materialize(
    true_rec: dict,
    source: str,
    source_id: str,
    force_issues: dict | None = None,
) -> dict:
    """Create a source-specific version of a canonical customer."""
    rec = {
        "source_customer_id": source_id,
        "true_id": true_rec["true_id"],
        "full_name": true_rec["full_name"],
        "first_name": true_rec["first_name"],
        "last_name": true_rec["last_name"],
        "email": true_rec["email"],
        "phone": true_rec["phone"],
        "date_of_birth": true_rec["date_of_birth"],
        "address_line1": true_rec["address_line1"],
        "city": true_rec["city"],
        "country": true_rec["country"],
        "status": true_rec["status"],
        "source_system": source,
    }

    force_issues = force_issues or {}

    # --- Completeness injections ---
    if force_issues.get("missing_name") or (random.random() < COMPLETENESS_RATE * 0.15):
        rec["full_name"] = None
        rec["first_name"] = None
        rec["last_name"] = None
        log_issue("COMP-01", "customer", source_id, source, "full_name", None, "Missing full name", "Critical")

    if force_issues.get("missing_contact") or (random.random() < COMPLETENESS_RATE * 0.4):
        if random.random() < 0.6:
            rec["email"] = None
            log_issue("COMP-03", "customer", source_id, source, "email", None, "Missing email", "Medium")
        if random.random() < 0.5:
            rec["phone"] = None
            if rec["email"] is None:
                log_issue("COMP-02", "customer", source_id, source, "email+phone", None, "Missing both email and phone", "High")

    if force_issues.get("missing_dob") or (random.random() < COMPLETENESS_RATE * 0.3):
        rec["date_of_birth"] = None

    # --- Validity injections ---
    if force_issues.get("bad_email") or (random.random() < VALIDITY_RATE and rec["email"]):
        old = rec["email"]
        rec["email"] = mess_email(old)
        if rec["email"] != old:
            log_issue("VAL-01", "customer", source_id, source, "email", rec["email"], f"Invalid email (was {old})", "High")

    if force_issues.get("bad_phone") or (random.random() < VALIDITY_RATE * 0.8 and rec["phone"]):
        styles = ["spaced", "dashed", "messy"]
        rec["phone"] = kenyan_phone(random.choice(styles))
        log_issue("VAL-02", "customer", source_id, source, "phone", rec["phone"], "Non-standard phone format", "Medium")

    if force_issues.get("bad_dob") or (random.random() < VALIDITY_RATE * 0.5 and rec["date_of_birth"]):
        # Future or very old
        if random.random() < 0.5:
            rec["date_of_birth"] = (date.today() + timedelta(days=random.randint(30, 400))).isoformat()
            log_issue("VAL-03", "customer", source_id, source, "date_of_birth", rec["date_of_birth"], "Future DOB", "High")
        else:
            rec["date_of_birth"] = date(1890, random.randint(1, 12), random.randint(1, 28)).isoformat()
            log_issue("VAL-03", "customer", source_id, source, "date_of_birth", rec["date_of_birth"], "Implausible old DOB", "High")
            log_issue("ANOM-02", "customer", source_id, source, "date_of_birth", rec["date_of_birth"], "Implausible age", "High")

    # --- Name variation (for fuzzy matching) ---
    if random.random() < 0.18:
        style = random.choice(["last_first", "initial", "upper", "typo"])
        if style == "last_first" and rec["last_name"] and rec["first_name"]:
            rec["full_name"] = f"{rec['last_name']}, {rec['first_name']}"
        elif style == "initial" and rec["first_name"] and rec["last_name"]:
            rec["full_name"] = f"{rec['first_name'][0]}. {rec['last_name']}"
        elif style == "upper":
            rec["full_name"] = (rec["full_name"] or "").upper()
        elif style == "typo" and rec["full_name"]:
            chars = list(rec["full_name"])
            if len(chars) > 4:
                idx = random.randint(1, len(chars) - 2)
                chars[idx] = random.choice(string.ascii_lowercase)
                rec["full_name"] = "".join(chars)
                log_issue("CONS-04", "customer", source_id, source, "full_name", rec["full_name"], "Name variation / typo", "Medium")

    return rec


# ---------------------------------------------------------------------------
# 3. Build source-specific customer lists
# ---------------------------------------------------------------------------
print("Materializing CRM / ERP / Marketing customers...")

crm_records = []
erp_records = []
mkt_records = []
ground_truth_rows = []

# Decide which canonical entities appear in which sources
crm_true_ids = set(random.sample([c["true_id"] for c in canonical], int(N_CANONICAL_CUSTOMERS * CRM_COVERAGE)))
erp_true_ids = set(random.sample([c["true_id"] for c in canonical], int(N_CANONICAL_CUSTOMERS * ERP_COVERAGE)))
mkt_true_ids = set(random.sample([c["true_id"] for c in canonical], int(N_CANONICAL_CUSTOMERS * MKT_COVERAGE)))

true_lookup = {c["true_id"]: c for c in canonical}

# CRM
for tid in crm_true_ids:
    sid = f"CRM-{new_id()}"
    rec = materialize(true_lookup[tid], "CRM", sid)
    crm_records.append(rec)
    ground_truth_rows.append({"true_id": tid, "source": "CRM", "source_customer_id": sid, "entity_type": "customer"})

# ERP customers
for tid in erp_true_ids:
    sid = f"ERP-{new_id()}"
    rec = materialize(true_lookup[tid], "ERP", sid)
    erp_records.append(rec)
    ground_truth_rows.append({"true_id": tid, "source": "ERP", "source_customer_id": sid, "entity_type": "customer"})

# Marketing
for tid in mkt_true_ids:
    sid = f"MKT-{new_id()}"
    rec = materialize(true_lookup[tid], "MKT", sid)
    mkt_records.append(rec)
    ground_truth_rows.append({"true_id": tid, "source": "MKT", "source_customer_id": sid, "entity_type": "customer"})

# Inject a few within-source exact duplicates (UNIQ-01)
def inject_within_source_dups(records: list, source: str, n: int = 4):
    for _ in range(n):
        if len(records) < 2:
            break
        base = random.choice(records).copy()
        base["source_customer_id"] = f"{source}-DUP-{new_id()}"
        records.append(base)
        log_issue("UNIQ-01", "customer", base["source_customer_id"], source, "email/phone", base.get("email"), "Exact duplicate within source", "High")
        ground_truth_rows.append(
            {
                "true_id": base["true_id"],
                "source": source,
                "source_customer_id": base["source_customer_id"],
                "entity_type": "customer",
                "note": "within-source-duplicate",
            }
        )

inject_within_source_dups(crm_records, "CRM", 5)
inject_within_source_dups(mkt_records, "MKT", 6)

# Inject cross-source conflicts on shared entities (CONS-01/02/03)
shared = list(crm_true_ids & erp_true_ids)
conflict_targets = random.sample(shared, min(12, len(shared)))
for tid in conflict_targets:
    # Find the CRM and ERP versions and mutate one of them
    crm_rec = next(r for r in crm_records if r["true_id"] == tid)
    erp_rec = next(r for r in erp_records if r["true_id"] == tid)

    conflict_type = random.choice(["email", "phone", "dob", "email+phone"])
    if conflict_type in ("email", "email+phone"):
        new_email = f"conflict.{crm_rec['source_customer_id'][:6]}@elsewhere.com"
        erp_rec["email"] = new_email
        log_issue("CONS-01", "customer", erp_rec["source_customer_id"], "ERP", "email", new_email, f"Conflicts with CRM email {crm_rec.get('email')}", "High")
    if conflict_type in ("phone", "email+phone"):
        new_phone = kenyan_phone("e164")
        erp_rec["phone"] = new_phone
        log_issue("CONS-02", "customer", erp_rec["source_customer_id"], "ERP", "phone", new_phone, f"Conflicts with CRM phone {crm_rec.get('phone')}", "High")
    if conflict_type == "dob":
        new_dob = random_dob(25, 55).isoformat()
        erp_rec["date_of_birth"] = new_dob
        log_issue("CONS-03", "customer", erp_rec["source_customer_id"], "ERP", "date_of_birth", new_dob, f"Conflicts with CRM DOB {crm_rec.get('date_of_birth')}", "Critical")

# ---------------------------------------------------------------------------
# 4. ERP Transactions
# ---------------------------------------------------------------------------
print("Generating ERP transactions...")

tx_records = []
erp_customer_ids = [r["source_customer_id"] for r in erp_records]

for i in range(N_ERP_TRANSACTIONS):
    cust_sid = random.choice(erp_customer_ids)
    true_id = next(r["true_id"] for r in erp_records if r["source_customer_id"] == cust_sid)
    tx_id = f"TXN-{new_id()}"
    amount = round(random.uniform(5.0, 850.0), 2)
    currency = random.choices(CURRENCIES, weights=[0.55, 0.35, 0.10])[0]
    tx_date = fake.date_between(start_date="-18m", end_date="today")
    status = random.choices(TX_STATUSES, weights=[0.78, 0.12, 0.06, 0.04])[0]
    desc = random.choice(PRODUCTS)

    rec = {
        "source_transaction_id": tx_id,
        "source_customer_id": cust_sid,
        "true_customer_id": true_id,
        "transaction_date": tx_date.isoformat(),
        "amount": amount,
        "currency": currency,
        "description": desc,
        "status": status,
        "source_system": "ERP",
    }

    # Completeness
    if random.random() < COMPLETENESS_RATE * 0.4:
        rec["amount"] = None
        log_issue("COMP-04", "transaction", tx_id, "ERP", "amount", None, "Missing amount", "Critical")
    if random.random() < COMPLETENESS_RATE * 0.25:
        rec["transaction_date"] = None
        log_issue("COMP-05", "transaction", tx_id, "ERP", "transaction_date", None, "Missing date", "Critical")
    if random.random() < COMPLETENESS_RATE * 0.3:
        rec["currency"] = None
        log_issue("COMP-06", "transaction", tx_id, "ERP", "currency", None, "Missing currency", "High")

    # Validity / Anomaly
    if random.random() < VALIDITY_RATE * 0.6 and rec["amount"] is not None:
        if random.random() < 0.5:
            rec["amount"] = round(random.uniform(15000, 95000), 2)
            log_issue("VAL-04", "transaction", tx_id, "ERP", "amount", rec["amount"], "Extreme amount", "High")
            log_issue("ANOM-01", "transaction", tx_id, "ERP", "amount", rec["amount"], "Amount outlier", "Medium")
        else:
            rec["amount"] = -abs(rec["amount"])
            log_issue("VAL-04", "transaction", tx_id, "ERP", "amount", rec["amount"], "Negative amount", "High")

    if random.random() < VALIDITY_RATE * 0.3 and rec["currency"]:
        rec["currency"] = random.choice(["$$", "KES.", "UsD", "XXX"])
        log_issue("VAL-05", "transaction", tx_id, "ERP", "currency", rec["currency"], "Invalid currency code", "High")

    if random.random() < VALIDITY_RATE * 0.25:
        future = date.today() + timedelta(days=random.randint(5, 60))
        rec["transaction_date"] = future.isoformat()
        log_issue("VAL-06", "transaction", tx_id, "ERP", "transaction_date", rec["transaction_date"], "Future transaction date", "High")

    tx_records.append(rec)
    ground_truth_rows.append(
        {
            "true_id": true_id,
            "source": "ERP",
            "source_customer_id": cust_sid,
            "source_transaction_id": tx_id,
            "entity_type": "transaction",
        }
    )

# A few near-duplicate transactions (UNIQ-03)
for _ in range(8):
    base = random.choice([t for t in tx_records if t["amount"] is not None]).copy()
    base["source_transaction_id"] = f"TXN-DUP-{new_id()}"
    # slight date shift
    if base["transaction_date"]:
        d = date.fromisoformat(base["transaction_date"])
        base["transaction_date"] = (d + timedelta(days=random.choice([-1, 0, 1]))).isoformat()
    tx_records.append(base)
    log_issue("UNIQ-03", "transaction", base["source_transaction_id"], "ERP", "amount+date", base["amount"], "Potential duplicate transaction", "Medium")

# ---------------------------------------------------------------------------
# 5. Write files
# ---------------------------------------------------------------------------
print("Writing output files...")

crm_df = pd.DataFrame(crm_records)
erp_df = pd.DataFrame(erp_records)
mkt_df = pd.DataFrame(mkt_records)
tx_df = pd.DataFrame(tx_records)
gt_df = pd.DataFrame(ground_truth_rows)

# Column order for readability
cust_cols = [
    "source_customer_id", "full_name", "first_name", "last_name",
    "email", "phone", "date_of_birth", "address_line1", "city", "country",
    "status", "source_system", "true_id"
]
crm_df = crm_df[[c for c in cust_cols if c in crm_df.columns]]
erp_df = erp_df[[c for c in cust_cols if c in erp_df.columns]]
mkt_df = mkt_df[[c for c in cust_cols if c in mkt_df.columns]]

tx_cols = [
    "source_transaction_id", "source_customer_id", "transaction_date",
    "amount", "currency", "description", "status", "source_system", "true_customer_id"
]
tx_df = tx_df[[c for c in tx_cols if c in tx_df.columns]]

crm_df.to_csv(SAMPLES_PATH / "crm_customers.csv", index=False)
erp_df.to_csv(SAMPLES_PATH / "erp_customers.csv", index=False)
tx_df.to_csv(SAMPLES_PATH / "erp_transactions.csv", index=False)
mkt_df.to_excel(SAMPLES_PATH / "marketing_customers.xlsx", index=False)

gt_df.to_csv(GT_PATH / "ground_truth.csv", index=False)

with open(GT_PATH / "injected_issues.json", "w") as f:
    json.dump(injected_issues, f, indent=2, default=str)

# Data dictionary
dictionary = f"""# DataQ — Sample Data Dictionary

**Generated:** {datetime.utcnow().isoformat()}Z  
**Seed:** {SEED}  
**Industry:** E-commerce  
**Locale:** Kenyan-mixed  

## Files

| File | Rows | Description |
|------|------|-------------|
| `crm_customers.csv` | {len(crm_df)} | CRM customer master |
| `erp_customers.csv` | {len(erp_df)} | ERP customer master |
| `erp_transactions.csv` | {len(tx_df)} | ERP orders / payments |
| `marketing_customers.xlsx` | {len(mkt_df)} | Marketing list (Excel) |
| `ground_truth.csv` | {len(gt_df)} | True entity mappings |
| `injected_issues.json` | {len(injected_issues)} | Every deliberate quality issue |

## Customer columns
- `source_customer_id` — ID in the source system
- `full_name`, `first_name`, `last_name`
- `email`, `phone` (various Kenyan + international formats)
- `date_of_birth` (ISO or null / invalid)
- `address_line1`, `city`, `country` (ISO-ish)
- `status` — active / inactive / unknown
- `source_system` — CRM / ERP / MKT
- `true_id` — ground-truth entity key (for evaluation only; not present in real systems)

## Transaction columns
- `source_transaction_id`, `source_customer_id`
- `transaction_date`, `amount`, `currency` (KES / USD / EUR + invalid)
- `description`, `status`
- `true_customer_id` — links back to canonical customer

## Injected issue categories
See `injected_issues.json` for the full list with rule_id, record_id, and evidence.
"""
(GT_PATH / "data_dictionary.md").write_text(dictionary)

# ---------------------------------------------------------------------------
# 6. Summary
# ---------------------------------------------------------------------------
from collections import Counter
rule_counts = Counter(i["rule_id"] for i in injected_issues)

print("\n" + "=" * 60)
print("DataQ — Dataset Generation Summary")
print("=" * 60)
print(f"Canonical entities     : {N_CANONICAL_CUSTOMERS}")
print(f"CRM records            : {len(crm_df)}")
print(f"ERP customers          : {len(erp_df)}")
print(f"ERP transactions       : {len(tx_df)}")
print(f"Marketing records      : {len(mkt_df)}")
print()
print("Injected issues by rule:")
for rule, cnt in sorted(rule_counts.items()):
    print(f"  {rule:12} {cnt:4d}")
print("-" * 40)
print(f"TOTAL issues           : {len(injected_issues)}")
print(f"Ground-truth mappings  : {len(gt_df)}")
print()
print(f"Output written to:")
print(f"  {SAMPLES_PATH}")
print(f"  {GT_PATH}")
print("=" * 60)
print("Done. You can now load these files into DataQ.")
