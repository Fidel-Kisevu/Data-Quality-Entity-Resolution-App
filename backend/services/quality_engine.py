"""
Quality Rules Engine — Phase 0 spec, Section 7.

Implements all rules from the DataQ Phase 0 Specification Pack:
- Completeness  COMP-01 .. COMP-06
- Validity      VAL-01  .. VAL-06
- Uniqueness    UNIQ-01, UNIQ-02  (UNIQ-03 deferred until matching populates customer_id)
- Consistency   CONS-01 .. CONS-05
- Anomaly       ANOM-01, ANOM-02

Design:
- Each rule is a self-contained function that queries the DB for offending
  rows and yields (rule_id, entity_type, record_id, severity, message, evidence).
- Runner persists one QualityFinding per offending record.
- CONS-01 .. CONS-04 emit ONE finding per conflict group, listing all
  conflicting records in evidence["related_record_ids"].
- UNIQ-02 only flags WITHIN-source email duplicates. Cross-source email
  overlap is a matching candidate (Section 8), not a quality problem.
- Runner writes an AuditEvent summarising the run.
"""
from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal
from typing import Iterator

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.models import (
    Customer,
    Transaction,
    QualityFinding,
    AuditEvent,
)


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

Finding = dict  # {rule_id, entity_type, record_id, severity, message, evidence}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
PHONE_RE = re.compile(r"^\+?[0-9]{7,15}$")
CURRENCY_RE = re.compile(r"^[A-Z]{3}$")

VALID_CURRENCIES = {"USD", "EUR", "GBP", "KES", "TZS", "UGX", "ZAR", "NGN"}


def _today() -> date:
    return date.today()


def _age(dob: date) -> int:
    today = _today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


# ---------------------------------------------------------------------------
# COMPLETENESS
# ---------------------------------------------------------------------------

def rule_comp_01(db: Session) -> Iterator[Finding]:
    """COMP-01: Missing full name → Critical."""
    rows = db.query(Customer).filter(
        (Customer.full_name.is_(None)) | (Customer.full_name == "")
    ).all()
    for c in rows:
        yield {
            "rule_id": "COMP-01",
            "entity_type": "customer",
            "record_id": c.id,
            "severity": "Critical",
            "message": "Customer is missing full name",
            "evidence": {"full_name": c.full_name},
        }


def rule_comp_02(db: Session) -> Iterator[Finding]:
    """COMP-02: Missing both email AND phone → High."""
    rows = db.query(Customer).filter(
        ((Customer.email.is_(None)) | (Customer.email == "")) &
        ((Customer.phone.is_(None)) | (Customer.phone == ""))
    ).all()
    for c in rows:
        yield {
            "rule_id": "COMP-02",
            "entity_type": "customer",
            "record_id": c.id,
            "severity": "High",
            "message": "Customer has neither email nor phone",
            "evidence": {"email": c.email, "phone": c.phone},
        }


def rule_comp_03(db: Session) -> Iterator[Finding]:
    """COMP-03: Missing email (but phone present) → Medium."""
    rows = db.query(Customer).filter(
        ((Customer.email.is_(None)) | (Customer.email == "")) &
        (Customer.phone.isnot(None)) & (Customer.phone != "")
    ).all()
    for c in rows:
        yield {
            "rule_id": "COMP-03",
            "entity_type": "customer",
            "record_id": c.id,
            "severity": "Medium",
            "message": "Customer is missing email",
            "evidence": {"phone": c.phone},
        }


def rule_comp_04(db: Session) -> Iterator[Finding]:
    """COMP-04: Missing amount → Critical."""
    rows = db.query(Transaction).filter(Transaction.amount.is_(None)).all()
    for t in rows:
        yield {
            "rule_id": "COMP-04",
            "entity_type": "transaction",
            "record_id": t.id,
            "severity": "Critical",
            "message": "Transaction is missing amount",
            "evidence": {"source_transaction_id": t.source_transaction_id},
        }


def rule_comp_05(db: Session) -> Iterator[Finding]:
    """COMP-05: Missing transaction date → Critical."""
    rows = db.query(Transaction).filter(Transaction.transaction_date.is_(None)).all()
    for t in rows:
        yield {
            "rule_id": "COMP-05",
            "entity_type": "transaction",
            "record_id": t.id,
            "severity": "Critical",
            "message": "Transaction is missing date",
            "evidence": {"source_transaction_id": t.source_transaction_id},
        }


def rule_comp_06(db: Session) -> Iterator[Finding]:
    """COMP-06: Missing currency → High."""
    rows = db.query(Transaction).filter(
        (Transaction.currency.is_(None)) | (Transaction.currency == "")
    ).all()
    for t in rows:
        yield {
            "rule_id": "COMP-06",
            "entity_type": "transaction",
            "record_id": t.id,
            "severity": "High",
            "message": "Transaction is missing currency",
            "evidence": {"amount": str(t.amount) if t.amount else None},
        }


# ---------------------------------------------------------------------------
# VALIDITY
# ---------------------------------------------------------------------------

def rule_val_01(db: Session) -> Iterator[Finding]:
    """VAL-01: Invalid email format → High."""
    rows = db.query(Customer).filter(
        Customer.email.isnot(None), Customer.email != ""
    ).all()
    for c in rows:
        if not EMAIL_RE.match(c.email or ""):
            yield {
                "rule_id": "VAL-01",
                "entity_type": "customer",
                "record_id": c.id,
                "severity": "High",
                "message": f"Invalid email format: {c.email}",
                "evidence": {"email": c.email},
            }


def rule_val_02(db: Session) -> Iterator[Finding]:
    """VAL-02: Invalid phone format → Medium."""
    rows = db.query(Customer).filter(
        Customer.phone.isnot(None), Customer.phone != ""
    ).all()
    for c in rows:
        cleaned = re.sub(r"[\s\-()]", "", c.phone or "")
        if not PHONE_RE.match(cleaned):
            yield {
                "rule_id": "VAL-02",
                "entity_type": "customer",
                "record_id": c.id,
                "severity": "Medium",
                "message": f"Invalid phone format: {c.phone}",
                "evidence": {"phone": c.phone},
            }


def rule_val_03(db: Session) -> Iterator[Finding]:
    """VAL-03: Invalid / future / too-old DOB → High."""
    rows = db.query(Customer).filter(Customer.date_of_birth.isnot(None)).all()
    today = _today()
    for c in rows:
        dob = c.date_of_birth
        if dob is None:
            continue
        if dob > today:
            yield {
                "rule_id": "VAL-03",
                "entity_type": "customer",
                "record_id": c.id,
                "severity": "High",
                "message": f"Date of birth is in the future: {dob}",
                "evidence": {"date_of_birth": str(dob)},
            }
        elif _age(dob) > 120:
            yield {
                "rule_id": "VAL-03",
                "entity_type": "customer",
                "record_id": c.id,
                "severity": "High",
                "message": f"Implausible age: {_age(dob)} years",
                "evidence": {"date_of_birth": str(dob), "age": _age(dob)},
            }


def rule_val_04(db: Session) -> Iterator[Finding]:
    """VAL-04: Invalid amount (≤ 0 or extreme) → High."""
    rows = db.query(Transaction).filter(Transaction.amount.isnot(None)).all()
    for t in rows:
        amt = t.amount
        if amt is None:
            continue
        if amt <= 0:
            yield {
                "rule_id": "VAL-04",
                "entity_type": "transaction",
                "record_id": t.id,
                "severity": "High",
                "message": f"Non-positive amount: {amt}",
                "evidence": {"amount": str(amt)},
            }
        elif amt > Decimal("1000000"):
            yield {
                "rule_id": "VAL-04",
                "entity_type": "transaction",
                "record_id": t.id,
                "severity": "High",
                "message": f"Extreme amount: {amt}",
                "evidence": {"amount": str(amt)},
            }


def rule_val_05(db: Session) -> Iterator[Finding]:
    """VAL-05: Invalid currency code → High."""
    rows = db.query(Transaction).filter(
        Transaction.currency.isnot(None), Transaction.currency != ""
    ).all()
    for t in rows:
        cur = (t.currency or "").strip().upper()
        if not CURRENCY_RE.match(cur) or cur not in VALID_CURRENCIES:
            yield {
                "rule_id": "VAL-05",
                "entity_type": "transaction",
                "record_id": t.id,
                "severity": "High",
                "message": f"Invalid currency code: {t.currency}",
                "evidence": {"currency": t.currency},
            }


def rule_val_06(db: Session) -> Iterator[Finding]:
    """VAL-06: Future transaction date → High."""
    rows = db.query(Transaction).filter(Transaction.transaction_date.isnot(None)).all()
    today = _today()
    for t in rows:
        if t.transaction_date and t.transaction_date > today:
            yield {
                "rule_id": "VAL-06",
                "entity_type": "transaction",
                "record_id": t.id,
                "severity": "High",
                "message": f"Future transaction date: {t.transaction_date}",
                "evidence": {"transaction_date": str(t.transaction_date)},
            }


# ---------------------------------------------------------------------------
# UNIQUENESS
# ---------------------------------------------------------------------------

def rule_uniq_01(db: Session) -> Iterator[Finding]:
    """
    UNIQ-01: Exact duplicate within source.
    Groups by (source_system, full_name, email). If the same person tuple
    appears more than once inside the same source, flag every copy.
    """
    rows = (
        db.query(
            Customer.source_system,
            Customer.full_name,
            Customer.email,
            func.count(Customer.id).label("cnt"),
        )
        .filter(Customer.full_name.isnot(None))
        .group_by(Customer.source_system, Customer.full_name, Customer.email)
        .having(func.count(Customer.id) > 1)
        .all()
    )
    for source_system, full_name, email, cnt in rows:
        dupes = db.query(Customer).filter(
            Customer.source_system == source_system,
            Customer.full_name == full_name,
            Customer.email == email,
        ).all()
        record_ids = [c.id for c in dupes]
        for c in dupes:
            yield {
                "rule_id": "UNIQ-01",
                "entity_type": "customer",
                "record_id": c.id,
                "severity": "High",
                "message": (
                    f"Duplicate within {source_system}: "
                    f"{full_name} / {email} ({cnt} copies)"
                ),
                "evidence": {
                    "source_system": source_system,
                    "full_name": full_name,
                    "email": email,
                    "duplicate_count": cnt,
                    "related_record_ids": record_ids,
                },
            }


def rule_uniq_02(db: Session) -> Iterator[Finding]:
    """
    UNIQ-02: Exact duplicate email WITHIN the same source.
    Cross-source email overlap is a MATCHING candidate (Section 8),
    NOT a quality problem — so it's excluded here.
    """
    rows = (
        db.query(
            Customer.source_system,
            Customer.email,
            func.count(Customer.id).label("cnt"),
        )
        .filter(Customer.email.isnot(None), Customer.email != "")
        .group_by(Customer.source_system, Customer.email)
        .having(func.count(Customer.id) > 1)
        .all()
    )
    for source_system, email, cnt in rows:
        dupes = db.query(Customer).filter(
            Customer.source_system == source_system,
            Customer.email == email,
        ).all()
        record_ids = [c.id for c in dupes]
        for c in dupes:
            yield {
                "rule_id": "UNIQ-02",
                "entity_type": "customer",
                "record_id": c.id,
                "severity": "High",
                "message": (
                    f"Email {email} appears {cnt} times within {source_system}"
                ),
                "evidence": {
                    "source_system": source_system,
                    "email": email,
                    "duplicate_count": cnt,
                    "related_record_ids": record_ids,
                },
            }


def rule_uniq_03(db: Session) -> Iterator[Finding]:
    """
    UNIQ-03: Potential duplicate transaction.
    Requires Transaction.customer_id to be populated (done by matching engine).
    Until then, this rule yields nothing.
    """
    groups = (
        db.query(
            Transaction.customer_id,
            Transaction.amount,
            Transaction.transaction_date,
            func.count(Transaction.id).label("cnt"),
        )
        .filter(
            Transaction.customer_id.isnot(None),
            Transaction.amount.isnot(None),
            Transaction.transaction_date.isnot(None),
        )
        .group_by(
            Transaction.customer_id,
            Transaction.amount,
            Transaction.transaction_date,
        )
        .having(func.count(Transaction.id) > 1)
        .all()
    )
    for cust_id, amount, txn_date, cnt in groups:
        dupes = db.query(Transaction).filter(
            Transaction.customer_id == cust_id,
            Transaction.amount == amount,
            Transaction.transaction_date == txn_date,
        ).all()
        record_ids = [t.id for t in dupes]
        for t in dupes:
            yield {
                "rule_id": "UNIQ-03",
                "entity_type": "transaction",
                "record_id": t.id,
                "severity": "Medium",
                "message": (
                    f"Potential duplicate transaction: {amount} on {txn_date} "
                    f"({cnt} matches)"
                ),
                "evidence": {
                    "customer_id": cust_id,
                    "amount": str(amount),
                    "transaction_date": str(txn_date),
                    "duplicate_count": cnt,
                    "related_record_ids": record_ids,
                },
            }


# ---------------------------------------------------------------------------
# CONSISTENCY (cross-source conflicts on the same customer)
# ---------------------------------------------------------------------------

def rule_cons_01(db: Session) -> Iterator[Finding]:
    """
    CONS-01: Conflicting email across sources → High.
    Group by phone; within a group, if emails differ → ONE finding per group.
    """
    phone_groups = (
        db.query(Customer.phone)
        .filter(Customer.phone.isnot(None), Customer.phone != "")
        .group_by(Customer.phone)
        .having(func.count(Customer.id) > 1)
        .all()
    )
    for (phone,) in phone_groups:
        group = db.query(Customer).filter(Customer.phone == phone).all()
        emails = {c.email for c in group if c.email}
        if len(emails) > 1:
            record_ids = [c.id for c in group]
            yield {
                "rule_id": "CONS-01",
                "entity_type": "customer",
                "record_id": record_ids[0],
                "severity": "High",
                "message": (
                    f"Conflicting email across sources (phone={phone}, "
                    f"{len(emails)} values)"
                ),
                "evidence": {
                    "phone": phone,
                    "field": "email",
                    "conflicting_values": sorted(emails),
                    "related_record_ids": record_ids,
                },
            }


def rule_cons_02(db: Session) -> Iterator[Finding]:
    """CONS-02: Conflicting phone across sources → High. Group by email."""
    email_groups = (
        db.query(Customer.email)
        .filter(Customer.email.isnot(None), Customer.email != "")
        .group_by(Customer.email)
        .having(func.count(Customer.id) > 1)
        .all()
    )
    for (email,) in email_groups:
        group = db.query(Customer).filter(Customer.email == email).all()
        phones = {c.phone for c in group if c.phone}
        if len(phones) > 1:
            record_ids = [c.id for c in group]
            yield {
                "rule_id": "CONS-02",
                "entity_type": "customer",
                "record_id": record_ids[0],
                "severity": "High",
                "message": (
                    f"Conflicting phone across sources (email={email}, "
                    f"{len(phones)} values)"
                ),
                "evidence": {
                    "email": email,
                    "field": "phone",
                    "conflicting_values": sorted(phones),
                    "related_record_ids": record_ids,
                },
            }


def rule_cons_03(db: Session) -> Iterator[Finding]:
    """CONS-03: Conflicting date of birth across sources → Critical. Group by email."""
    email_groups = (
        db.query(Customer.email)
        .filter(Customer.email.isnot(None), Customer.email != "")
        .group_by(Customer.email)
        .having(func.count(Customer.id) > 1)
        .all()
    )
    for (email,) in email_groups:
        group = db.query(Customer).filter(Customer.email == email).all()
        dobs = {c.date_of_birth for c in group if c.date_of_birth}
        if len(dobs) > 1:
            record_ids = [c.id for c in group]
            yield {
                "rule_id": "CONS-03",
                "entity_type": "customer",
                "record_id": record_ids[0],
                "severity": "Critical",
                "message": (
                    f"Conflicting DOB across sources (email={email}, "
                    f"{len(dobs)} values)"
                ),
                "evidence": {
                    "email": email,
                    "field": "date_of_birth",
                    "conflicting_values": sorted(str(v) for v in dobs),
                    "related_record_ids": record_ids,
                },
            }


def rule_cons_04(db: Session) -> Iterator[Finding]:
    """
    CONS-04: Name variation across sources → Medium.
    Group by email; flag if full_name values differ.
    """
    email_groups = (
        db.query(Customer.email)
        .filter(Customer.email.isnot(None), Customer.email != "")
        .group_by(Customer.email)
        .having(func.count(Customer.id) > 1)
        .all()
    )
    for (email,) in email_groups:
        group = db.query(Customer).filter(Customer.email == email).all()
        names = {c.full_name for c in group if c.full_name}
        if len(names) > 1:
            record_ids = [c.id for c in group]
            yield {
                "rule_id": "CONS-04",
                "entity_type": "customer",
                "record_id": record_ids[0],
                "severity": "Medium",
                "message": (
                    f"Name variation across sources (email={email}, "
                    f"{len(names)} distinct names)"
                ),
                "evidence": {
                    "email": email,
                    "field": "full_name",
                    "conflicting_values": sorted(names),
                    "related_record_ids": record_ids,
                },
            }


def rule_cons_05(db: Session) -> Iterator[Finding]:
    """CONS-05: Amount conflict on matched transaction → Critical."""
    groups = (
        db.query(Transaction.source_transaction_id)
        .filter(Transaction.source_transaction_id.isnot(None))
        .group_by(Transaction.source_transaction_id)
        .having(func.count(Transaction.id) > 1)
        .all()
    )
    for (src_txn_id,) in groups:
        group = db.query(Transaction).filter(
            Transaction.source_transaction_id == src_txn_id
        ).all()
        amounts = {t.amount for t in group if t.amount is not None}
        if len(amounts) > 1:
            record_ids = [t.id for t in group]
            yield {
                "rule_id": "CONS-05",
                "entity_type": "transaction",
                "record_id": record_ids[0],
                "severity": "Critical",
                "message": f"Amount conflict for txn {src_txn_id}",
                "evidence": {
                    "source_transaction_id": src_txn_id,
                    "conflicting_amounts": sorted(str(a) for a in amounts),
                    "related_record_ids": record_ids,
                },
            }


# ---------------------------------------------------------------------------
# ANOMALY
# ---------------------------------------------------------------------------

def rule_anom_01(db: Session) -> Iterator[Finding]:
    """ANOM-01: Extreme amount outlier (z-score > 3) → Medium."""
    rows = db.query(Transaction).filter(Transaction.amount.isnot(None)).all()
    amounts = [float(t.amount) for t in rows if t.amount is not None]
    if len(amounts) < 10:
        return
    mean = sum(amounts) / len(amounts)
    var = sum((a - mean) ** 2 for a in amounts) / len(amounts)
    std = var ** 0.5
    if std == 0:
        return
    for t in rows:
        if t.amount is None:
            continue
        z = abs((float(t.amount) - mean) / std)
        if z > 3:
            yield {
                "rule_id": "ANOM-01",
                "entity_type": "transaction",
                "record_id": t.id,
                "severity": "Medium",
                "message": f"Amount outlier (z={z:.2f}): {t.amount}",
                "evidence": {
                    "amount": str(t.amount),
                    "z_score": round(z, 2),
                    "mean": round(mean, 2),
                    "std": round(std, 2),
                },
            }


def rule_anom_02(db: Session) -> Iterator[Finding]:
    """ANOM-02: Implausible age → High."""
    rows = db.query(Customer).filter(Customer.date_of_birth.isnot(None)).all()
    for c in rows:
        age = _age(c.date_of_birth)
        if age < 0 or age > 120:
            yield {
                "rule_id": "ANOM-02",
                "entity_type": "customer",
                "record_id": c.id,
                "severity": "High",
                "message": f"Implausible age: {age}",
                "evidence": {"date_of_birth": str(c.date_of_birth), "age": age},
            }


# ---------------------------------------------------------------------------
# Registry & Runner
# ---------------------------------------------------------------------------

# UNIQ-03 is disabled until the matching engine populates Transaction.customer_id.
# It is defined above but intentionally omitted from this list.
ALL_RULES = [
    rule_comp_01, rule_comp_02, rule_comp_03, rule_comp_04, rule_comp_05, rule_comp_06,
    rule_val_01, rule_val_02, rule_val_03, rule_val_04, rule_val_05, rule_val_06,
    rule_uniq_01, rule_uniq_02,  # rule_uniq_03 — disabled until matching runs
    rule_cons_01, rule_cons_02, rule_cons_03, rule_cons_04, rule_cons_05,
    rule_anom_01, rule_anom_02,
]


def run_quality_checks(db: Session) -> dict:
    """
    Execute every rule. Persist one QualityFinding per offending record.
    Write an AuditEvent summarising the run.

    Returns summary: {run_at, rules_run, findings_created, by_rule, by_severity}
    """
    run_at = datetime.utcnow()

    # Clear previous OPEN findings so runs are idempotent
    db.query(QualityFinding).filter(QualityFinding.status == "open").delete()
    db.flush()

    findings_created = 0
    by_rule: dict[str, int] = {}
    by_severity: dict[str, int] = {}

    for rule_fn in ALL_RULES:
        for f in rule_fn(db):
            db.add(QualityFinding(
                rule_id=f["rule_id"],
                entity_type=f["entity_type"],
                record_id=f["record_id"],
                severity=f["severity"],
                message=f["message"],
                evidence=f.get("evidence"),
                status="open",
                created_at=run_at,
            ))
            findings_created += 1
            by_rule[f["rule_id"]] = by_rule.get(f["rule_id"], 0) + 1
            by_severity[f["severity"]] = by_severity.get(f["severity"], 0) + 1

    # Audit event
    db.add(AuditEvent(
        event_type="quality.run",
        entity_type=None,
        entity_id=None,
        actor="system",
        action="run_quality_checks",
        before_state=None,
        after_state={
            "findings_created": findings_created,
            "by_rule": by_rule,
            "by_severity": by_severity,
        },
        notes=f"Quality run created {findings_created} findings",
    ))

    db.commit()

    return {
        "run_at": run_at.isoformat(),
        "rules_run": len(ALL_RULES),
        "findings_created": findings_created,
        "by_rule": by_rule,
        "by_severity": by_severity,
    }