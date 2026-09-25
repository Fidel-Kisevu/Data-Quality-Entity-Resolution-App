"""
Link transactions to their trusted customers.

Chain:
    Transaction.source_customer_id
        -> Customer.source_customer_id   (raw ERP customer)
        -> Customer.trusted_customer_id  (survivor pointer)
        -> Trusted Customer.id
"""
from __future__ import annotations

from datetime import datetime
from sqlalchemy.orm import Session

from models.models import Customer, Transaction, AuditEvent


def link_transactions_to_trusted_customers(db: Session) -> dict:
    """
    Populate Transaction.customer_id by walking the transaction's
    source_customer_id -> raw Customer -> trusted Customer chain.

    Idempotent: re-running produces the same result.
    """
    # 1. Build lookup: (source_system, source_customer_id) -> trusted_customer_id
    raw_customers = (
        db.query(
            Customer.source_system,
            Customer.source_customer_id,
            Customer.id,
            Customer.trusted_customer_id,
        )
        .filter(Customer.source_customer_id.isnot(None))
        .all()
    )

    lookup: dict[tuple[str, str], str] = {}
    for source_system, source_customer_id, customer_id, trusted_id in raw_customers:
        # A trusted customer is either is_trusted=True (its own id) or has
        # trusted_customer_id pointing to the survivor
        if trusted_id:
            lookup[(source_system or "", source_customer_id)] = trusted_id
        else:
            # Not part of a group — points to itself (still valid as a customer_id)
            lookup[(source_system or "", source_customer_id)] = customer_id

    # 2. Iterate transactions, assign customer_id
    transactions = db.query(Transaction).all()
    linked = 0
    already_linked = 0
    unresolved = 0

    for t in transactions:
        if t.customer_id:
            already_linked += 1
            continue

        # Transaction's source_customer_id was captured during ingestion
        src_key = (t.source_system or "", t.source_customer_id or "")
        target = lookup.get(src_key)

        if target:
            t.customer_id = target
            t.updated_at = datetime.utcnow()
            linked += 1
        else:
            unresolved += 1

    # 3. Audit event
    db.add(AuditEvent(
        event_type="transactions.linked",
        entity_type=None,
        entity_id=None,
        actor="system",
        action="link_transactions",
        before_state=None,
        after_state={
            "total_transactions": len(transactions),
            "newly_linked": linked,
            "already_linked": already_linked,
            "unresolved": unresolved,
            "lookup_size": len(lookup),
        },
        notes=f"Linked {linked} transactions to trusted customers",
    ))
    db.commit()

    return {
        "total_transactions": len(transactions),
        "newly_linked": linked,
        "already_linked": already_linked,
        "unresolved": unresolved,
        "lookup_size": len(lookup),
    }