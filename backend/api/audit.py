from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from core.database import get_db
from models.models import AuditEvent

router = APIRouter()


@router.get("")
def list_audit_events(
    event_type: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    actor: Optional[str] = Query(None),
    since: Optional[str] = Query(None, description="ISO datetime"),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
):
    q = db.query(AuditEvent)
    if event_type:
        q = q.filter(AuditEvent.event_type == event_type)
    if entity_type:
        q = q.filter(AuditEvent.entity_type == entity_type)
    if entity_id:
        q = q.filter(AuditEvent.entity_id == entity_id)
    if actor:
        q = q.filter(AuditEvent.actor == actor)
    if since:
        try:
            dt = datetime.fromisoformat(since)
            q = q.filter(AuditEvent.created_at >= dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid `since` datetime")

    total = q.count()
    rows = q.order_by(AuditEvent.created_at.desc()).limit(limit).all()
    return {
        "total": total,
        "returned": len(rows),
        "events": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "entity_type": e.entity_type,
                "entity_id": e.entity_id,
                "actor": e.actor,
                "action": e.action,
                "before_state": e.before_state,
                "after_state": e.after_state,
                "notes": e.notes,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in rows
        ],
    }


@router.get("/record/{record_id}")
def audit_for_record(record_id: str, db: Session = Depends(get_db)):
    """Full audit history for one record (customer, transaction, match group, exception)."""
    rows = (
        db.query(AuditEvent)
        .filter(AuditEvent.entity_id == record_id)
        .order_by(AuditEvent.created_at.asc())
        .all()
    )
    return {
        "record_id": record_id,
        "event_count": len(rows),
        "events": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "actor": e.actor,
                "action": e.action,
                "before_state": e.before_state,
                "after_state": e.after_state,
                "notes": e.notes,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in rows
        ],
    }


@router.get("/summary")
def audit_summary(db: Session = Depends(get_db)):
    """Counts by event_type and actor."""
    from sqlalchemy import func
    by_type = dict(
        db.query(AuditEvent.event_type, func.count(AuditEvent.id))
        .group_by(AuditEvent.event_type)
        .all()
    )
    by_actor = dict(
        db.query(AuditEvent.actor, func.count(AuditEvent.id))
        .group_by(AuditEvent.actor)
        .all()
    )
    return {
        "total_events": db.query(AuditEvent).count(),
        "by_event_type": by_type,
        "by_actor": by_actor,
    }