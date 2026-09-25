from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from core.database import get_db
from models.models import MatchGroup, Customer, ExceptionRecord, AuditEvent
from services.matching import run_customer_matching
from services.survivorship import build_survivorship_values, pick_surviving_record


router = APIRouter()


@router.post("/run")
def run_matching(db: Session = Depends(get_db)):
    """Build customer MatchGroups from all ingested customers."""
    return run_customer_matching(db)


@router.get("/groups")
def list_groups(
    match_type: Optional[str] = Query(None),
    status: Optional[str] = Query("needs_review"),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
):
    q = db.query(MatchGroup).filter(MatchGroup.entity_type == "customer")
    if match_type:
        q = q.filter(MatchGroup.match_type == match_type)
    if status:
        q = q.filter(MatchGroup.status == status)

    total = q.count()
    rows = q.order_by(MatchGroup.confidence_score.desc()).limit(limit).all()

    return {
        "total": total,
        "returned": len(rows),
        "groups": [
            {
                "id": g.id,
                "match_type": g.match_type,
                "confidence_score": g.confidence_score,
                "status": g.status,
                "record_ids": g.record_ids,
                "evidence": g.evidence,
                "created_at": g.created_at.isoformat() if g.created_at else None,
            }
            for g in rows
        ],
    }


@router.get("/groups/{group_id}")
def get_group(group_id: str, db: Session = Depends(get_db)):
    g = db.query(MatchGroup).filter(MatchGroup.id == group_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Match group not found")

    record_ids = g.record_ids or []
    customers = db.query(Customer).filter(Customer.id.in_(record_ids)).all()
    if not customers:
        raise HTTPException(status_code=404, detail="Records not found")

    # Suggest a survivor
    survivor = pick_surviving_record(customers)
    survivorship = build_survivorship_values(customers)

    return {
        "id": g.id,
        "match_type": g.match_type,
        "confidence_score": g.confidence_score,
        "status": g.status,
        "evidence": g.evidence,
        "records": [
            {
                "id": c.id,
                "source_system": c.source_system,
                "source_customer_id": c.source_customer_id,
                "full_name": c.full_name,
                "email": c.email,
                "phone": c.phone,
                "date_of_birth": str(c.date_of_birth) if c.date_of_birth else None,
                "address_line1": c.address_line1,
                "city": c.city,
                "country": c.country,
                "status": c.status,
                "is_survivor_suggestion": c.id == survivor.id,
            }
            for c in customers
        ],
        "survivorship_suggestion": survivorship,
    }


@router.post("/groups/{group_id}/resolve")
def resolve_group(
    group_id: str,
    decision: dict,
    db: Session = Depends(get_db),
):
    """
    Resolve a match group.

    Body:
      {
        "action": "accept_survivor" | "reject_match" | "manual_merge",
        "notes": "optional string",
        "override_values": {"email": "...", ...}   # only for manual_merge
      }
    """
    g = db.query(MatchGroup).filter(MatchGroup.id == group_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Match group not found")

    action = decision.get("action")
    if action not in ("accept_survivor", "reject_match", "manual_merge"):
        raise HTTPException(status_code=400, detail="Invalid action")

    record_ids = g.record_ids or []
    customers = db.query(Customer).filter(Customer.id.in_(record_ids)).all()
    if not customers:
        raise HTTPException(status_code=404, detail="Records not found")

    before_state = {
        "status": g.status,
        "record_ids": record_ids,
        "confidence_score": g.confidence_score,
    }

    if action == "reject_match":
        # No records merged; just close the group
        g.status = "resolved"
        g.updated_at = __import__("datetime").datetime.utcnow()

        # Mark records as reviewed (but not merged)
        for c in customers:
            c.is_manually_reviewed = True
            c.updated_at = __import__("datetime").datetime.utcnow()

        notes = decision.get("notes", "Rejected match — records kept separate")

    elif action == "accept_survivor":
        survivor = pick_surviving_record(customers)
        survivorship = build_survivorship_values(customers)

        # Mark survivor as trusted
        survivor.is_trusted = True
        survivor.is_manually_reviewed = True
        survivor.confidence_score = g.confidence_score
        survivor.trusted_customer_id = survivor.id
        survivor.updated_at = __import__("datetime").datetime.utcnow()

        # Apply survivorship values to the survivor record
        for field, value in survivorship["values"].items():
            if value is not None:
                setattr(survivor, field, value)

        # Mark others as duplicates pointing to survivor
        for c in customers:
            if c.id == survivor.id:
                continue
            c.trusted_customer_id = survivor.id
            c.is_manually_reviewed = True
            c.updated_at = __import__("datetime").datetime.utcnow()

        g.status = "resolved"
        g.proposed_surviving_id = survivor.id
        g.updated_at = __import__("datetime").datetime.utcnow()
        notes = decision.get("notes", f"Accepted survivor {survivor.id}")

    else:  # manual_merge
        override_values = decision.get("override_values") or {}
        survivor = pick_surviving_record(customers)
        survivor.is_trusted = True
        survivor.is_manually_reviewed = True
        survivor.confidence_score = g.confidence_score
        survivor.trusted_customer_id = survivor.id
        survivor.updated_at = __import__("datetime").datetime.utcnow()

        for field, value in override_values.items():
            if hasattr(survivor, field):
                setattr(survivor, field, value)

        for c in customers:
            if c.id == survivor.id:
                continue
            c.trusted_customer_id = survivor.id
            c.is_manually_reviewed = True
            c.updated_at = __import__("datetime").datetime.utcnow()

        g.status = "resolved"
        g.proposed_surviving_id = survivor.id
        g.updated_at = __import__("datetime").datetime.utcnow()
        notes = decision.get("notes", f"Manual merge — survivor {survivor.id}")

    # Resolve any linked exceptions
    db.query(ExceptionRecord).filter(
        ExceptionRecord.group_id == group_id,
        ExceptionRecord.status == "new",
    ).update({
        ExceptionRecord.status: "resolved",
        ExceptionRecord.resolution_decision: action,
        ExceptionRecord.resolution_notes: notes,
        ExceptionRecord.resolved_at: __import__("datetime").datetime.utcnow(),
    })

    # Audit
    db.add(AuditEvent(
        event_type="matching.resolve",
        entity_type="match_group",
        entity_id=g.id,
        actor="user",
        action=action,
        before_state=before_state,
        after_state={
            "status": g.status,
            "proposed_surviving_id": g.proposed_surviving_id,
            "notes": notes,
        },
        notes=notes,
    ))

    db.commit()

    return {
        "group_id": g.id,
        "status": g.status,
        "proposed_surviving_id": g.proposed_surviving_id,
        "action": action,
        "notes": notes,
    }
@router.post("/resolve-all")
def resolve_all(db: Session = Depends(get_db)):
    """
    Bulk-resolve every needs_review group by accepting the survivorship suggestion.
    Marks survivors as trusted and non-survivors as duplicates pointing to the survivor.
    """
    from services.survivorship import pick_surviving_record, build_survivorship_values

    groups = db.query(MatchGroup).filter(
        MatchGroup.status == "needs_review",
        MatchGroup.entity_type == "customer",
    ).all()

    resolved = 0
    survivors_marked = 0
    duplicates_marked = 0

    for g in groups:
        record_ids = g.record_ids or []
        customers = db.query(Customer).filter(Customer.id.in_(record_ids)).all()
        if len(customers) < 2:
            g.status = "resolved"
            g.updated_at = datetime.utcnow()
            continue

        survivor = pick_surviving_record(customers)
        survivorship = build_survivorship_values(customers)

        # Apply survivorship values to the survivor
        for field, value in survivorship["values"].items():
            if value is not None:
                setattr(survivor, field, value)

        survivor.is_trusted = True
        survivor.is_manually_reviewed = False  # bulk, so not manually reviewed
        survivor.confidence_score = g.confidence_score
        survivor.trusted_customer_id = survivor.id
        survivor.updated_at = datetime.utcnow()
        survivors_marked += 1

        for c in customers:
            if c.id == survivor.id:
                continue
            c.trusted_customer_id = survivor.id
            c.updated_at = datetime.utcnow()
            duplicates_marked += 1

        g.status = "resolved"
        g.proposed_surviving_id = survivor.id
        g.updated_at = datetime.utcnow()
        resolved += 1

    # Close any exceptions tied to now-resolved groups
    db.query(ExceptionRecord).filter(
        ExceptionRecord.status == "new",
    ).update({
        ExceptionRecord.status: "resolved",
        ExceptionRecord.resolution_decision: "bulk_accept_survivor",
        ExceptionRecord.resolution_notes: "Bulk resolution by /reconciliation/resolve-all",
        ExceptionRecord.resolved_at: datetime.utcnow(),
    })

    db.add(AuditEvent(
        event_type="matching.resolve_all",
        entity_type=None,
        entity_id=None,
        actor="system",
        action="resolve_all_groups",
        before_state=None,
        after_state={
            "groups_resolved": resolved,
            "survivors_marked": survivors_marked,
            "duplicates_marked": duplicates_marked,
        },
        notes=f"Bulk-resolved {resolved} groups",
    ))
    db.commit()

    return {
        "groups_resolved": resolved,
        "survivors_marked": survivors_marked,
        "duplicates_marked": duplicates_marked,
    }
@router.post("/link-transactions")
def link_transactions(db: Session = Depends(get_db)):
    """Populate Transaction.customer_id by walking the trusted-customer chain."""
    from services.transaction_linker import link_transactions_to_trusted_customers
    return link_transactions_to_trusted_customers(db)