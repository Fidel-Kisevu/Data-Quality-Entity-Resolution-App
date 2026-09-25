"""
Trusted Data service — Phase 0 spec, Section 5.8 & Section 13.

A trusted customer is one where:
- MatchGroup.status == "resolved" AND
- Customer.is_trusted == True

We also expose lineage: the source records that contributed to each trusted record.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from models.models import Customer, Transaction


def list_trusted_customers(
    db: Session,
    limit: int = 500,
    offset: int = 0,
) -> dict:
    """Return all trusted customers with lineage info."""
    base = db.query(Customer).filter(Customer.is_trusted == True)
    total = base.count()
    rows = base.order_by(Customer.full_name).offset(offset).limit(limit).all()

    customers = []
    for c in rows:
        # lineage: all source records that point to this survivor
        lineage_rows = db.query(Customer).filter(
            Customer.trusted_customer_id == c.id
        ).all()
        # include self as the first lineage entry
        lineage = [{
            "customer_id": c.id,
            "source_system": c.source_system,
            "source_customer_id": c.source_customer_id,
            "is_survivor": True,
        }]
        for l in lineage_rows:
            if l.id == c.id:
                continue
            lineage.append({
                "customer_id": l.id,
                "source_system": l.source_system,
                "source_customer_id": l.source_customer_id,
                "is_survivor": False,
            })

        customers.append({
            "id": c.id,
            "full_name": c.full_name,
            "email": c.email,
            "phone": c.phone,
            "date_of_birth": str(c.date_of_birth) if c.date_of_birth else None,
            "city": c.city,
            "country": c.country,
            "status": c.status,
            "confidence_score": c.confidence_score,
            "is_manually_reviewed": c.is_manually_reviewed,
            "lineage": lineage,
        })

    return {
        "total": total,
        "returned": len(customers),
        "offset": offset,
        "customers": customers,
    }


def get_trusted_customer(db: Session, customer_id: str) -> Optional[dict]:
    c = db.query(Customer).filter(Customer.id == customer_id, Customer.is_trusted == True).first()
    if not c:
        return None

    lineage_rows = db.query(Customer).filter(Customer.trusted_customer_id == c.id).all()
    lineage = [{
        "customer_id": c.id,
        "source_system": c.source_system,
        "source_customer_id": c.source_customer_id,
        "is_survivor": True,
    }]
    for l in lineage_rows:
        if l.id == c.id:
            continue
        lineage.append({
            "customer_id": l.id,
            "source_system": l.source_system,
            "source_customer_id": l.source_customer_id,
            "is_survivor": False,
        })

    # Linked transactions
    txns = db.query(Transaction).filter(Transaction.customer_id == c.id).all()

    return {
        "id": c.id,
        "full_name": c.full_name,
        "email": c.email,
        "phone": c.phone,
        "date_of_birth": str(c.date_of_birth) if c.date_of_birth else None,
        "address_line1": c.address_line1,
        "city": c.city,
        "country": c.country,
        "status": c.status,
        "confidence_score": c.confidence_score,
        "is_manually_reviewed": c.is_manually_reviewed,
        "lineage": lineage,
        "transactions": [
            {
                "id": t.id,
                "transaction_date": str(t.transaction_date) if t.transaction_date else None,
                "amount": str(t.amount) if t.amount else None,
                "currency": t.currency,
                "status": t.status,
                "source_system": t.source_system,
            }
            for t in txns
        ],
    }


def list_trusted_transactions(
    db: Session,
    limit: int = 500,
    offset: int = 0,
) -> dict:
    """
    Return transactions attached to trusted customers.
    For MVP, a transaction is 'trusted' if its customer_id points to a trusted customer.
    """
    trusted_ids = [c.id for c in db.query(Customer.id).filter(Customer.is_trusted == True).all()]
    # flatten
    trusted_ids = [row[0] if isinstance(row, tuple) else row for row in trusted_ids]

    q = db.query(Transaction).filter(Transaction.customer_id.in_(trusted_ids)) if trusted_ids else db.query(Transaction).filter(False)
    total = q.count()
    rows = q.order_by(Transaction.transaction_date.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "returned": len(rows),
        "offset": offset,
        "transactions": [
            {
                "id": t.id,
                "customer_id": t.customer_id,
                "transaction_date": str(t.transaction_date) if t.transaction_date else None,
                "amount": str(t.amount) if t.amount else None,
                "currency": t.currency,
                "status": t.status,
                "description": t.description,
                "source_system": t.source_system,
            }
            for t in rows
        ],
    }


def export_trusted_customers_csv(db: Session) -> str:
    """Return CSV text of trusted customers (flat, one row per trusted record)."""
    import csv
    from io import StringIO

    rows = db.query(Customer).filter(Customer.is_trusted == True).order_by(Customer.full_name).all()

    out = StringIO()
    writer = csv.writer(out)
    writer.writerow([
        "id", "full_name", "email", "phone", "date_of_birth",
        "address_line1", "city", "country", "status",
        "confidence_score", "is_manually_reviewed",
    ])
    for c in rows:
        writer.writerow([
            c.id, c.full_name, c.email, c.phone,
            c.date_of_birth.isoformat() if c.date_of_birth else "",
            c.address_line1, c.city, c.country, c.status,
            c.confidence_score, c.is_manually_reviewed,
        ])
    return out.getvalue()