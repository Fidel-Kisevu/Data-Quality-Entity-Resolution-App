from core.database import SessionLocal
from models.models import Customer, Transaction
import re
from collections import Counter

db = SessionLocal()

# --- VAL-02 investigation ---
PHONE_RE = re.compile(r"^\+?[0-9]{7,15}$")
phones = [c.phone for c in db.query(Customer).all() if c.phone]
bad = [p for p in phones if not PHONE_RE.match(re.sub(r"[\s\-()]", "", p))]
print(f"VAL-02: {len(bad)} invalid phones out of {len(phones)}")
print(f"  Samples: {bad[:5]}")

# --- VAL-01 investigation ---
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
emails = [c.email for c in db.query(Customer).all() if c.email]
bad_e = [e for e in emails if not EMAIL_RE.match(e)]
print(f"\nVAL-01: {len(bad_e)} invalid emails out of {len(emails)}")
print(f"  Samples: {bad_e[:5]}")

# --- UNIQ-01 investigation: within-source exact dupes ---
dupes = db.query(Customer.source_system, Customer.source_customer_id).all()
counts = Counter(dupes)
real_dupes = [(k, v) for k, v in counts.items() if v > 1]
print(f"\nUNIQ-01: {len(real_dupes)} source_customer_ids appear more than once")
print(f"  Samples: {real_dupes[:3]}")

# --- check customer_id null on transactions ---
txn_with_cust = db.query(Transaction).filter(Transaction.customer_id.isnot(None)).count()
txn_total = db.query(Transaction).count()
print(f"\nTransactions with customer_id set: {txn_with_cust}/{txn_total}")

# --- sample of source_system values on Customer ---
sys_counts = Counter(c.source_system for c in db.query(Customer).all())
print(f"\nCustomer.source_system distribution: {dict(sys_counts)}")

# --- check for cross-source emails ---
email_to_sources = {}
for c in db.query(Customer).all():
    if c.email:
        email_to_sources.setdefault(c.email, set()).add(c.source_system)
cross = {e: s for e, s in email_to_sources.items() if len(s) > 1}
print(f"\nEmails appearing in multiple source_systems: {len(cross)}")