from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

from core.database import get_db
from models.models import ExceptionRecord, AuditEvent

router = APIRouter()


class ExceptionUpdate(BaseModel):
    status: Optional[str] = None
    resolution_notes: Optional[str] = None
    assigned_to: Optional[str] = None


@router.get("")
def list_exceptions(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    exception_type: Optional[str] = Query(None),
    limit: int = Query(200, le=1000),
    db: Session = Depends(get_db),
):
    q = db.query(ExceptionRecord)
    if status:
        q = q.filter(ExceptionRecord.status == status)
    if severity:
        q = q.filter(ExceptionRecord.severity == severity)
    if exception_type:
        q = q.filter(ExceptionRecord.exception_type == exception_type)

    rows = q.order_by(ExceptionRecord.created_at.desc()).limit(limit).all()
    return [
        {
            "id": e.id,
            "exception_type": e.exception_type,
            "severity": e.severity,
            "status": e.status,
            "related_entity_type": e.related_entity_type,
            "related_record_ids": e.related_record_ids,
            "group_id": e.group_id,
            "title": e.title,
            "description": e.description,
            "system_suggestion": e.system_suggestion,
            "evidence": e.evidence,
            "resolution_decision": e.resolution_decision,
            "resolution_notes": e.resolution_notes,
            "created_at": e.created_at.isoformat() if e.created_at else None,
            "updated_at": e.updated_at.isoformat() if e.updated_at else None,
            "resolved_at": e.resolved_at.isoformat() if e.resolved_at else None,
        }
        for e in rows
    ]


@router.get("/{exception_id}")
def get_exception(exception_id: str, db: Session = Depends(get_db)):
    e = db.query(ExceptionRecord).filter(ExceptionRecord.id == exception_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Exception not found")
    return {
        "id": e.id,
        "exception_type": e.exception_type,
        "severity": e.severity,
        "status": e.status,
        "related_entity_type": e.related_entity_type,
        "related_record_ids": e.related_record_ids,
        "group_id": e.group_id,
        "title": e.title,
        "description": e.description,
        "system_suggestion": e.system_suggestion,
        "evidence": e.evidence,
        "resolution_decision": e.resolution_decision,
        "resolution_notes": e.resolution_notes,
        "created_at": e.created_at.isoformat() if e.created_at else None,
        "updated_at": e.updated_at.isoformat() if e.updated_at else None,
        "resolved_at": e.resolved_at.isoformat() if e.resolved_at else None,
    }


@router.patch("/{exception_id}")
def update_exception(
    exception_id: str,
    payload: ExceptionUpdate,
    db: Session = Depends(get_db),
):
    e = db.query(ExceptionRecord).filter(ExceptionRecord.id == exception_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Exception not found")

    before = {
        "status": e.status,
        "resolution_notes": e.resolution_notes,
        "assigned_to": e.assigned_to,
    }

    if payload.status is not None:
        e.status = payload.status
        if payload.status in ("resolved", "rejected"):
            e.resolved_at = datetime.utcnow()
            e.resolution_decision = payload.status
    if payload.resolution_notes is not None:
        e.resolution_notes = payload.resolution_notes
    if payload.assigned_to is not None:
        e.assigned_to = payload.assigned_to

    e.updated_at = datetime.utcnow()

    db.add(AuditEvent(
        event_type="exception.updated",
        entity_type="exception",
        entity_id=e.id,
        actor="user",
        action="update_exception",
        before_state=before,
        after_state={
            "status": e.status,
            "resolution_notes": e.resolution_notes,
            "assigned_to": e.assigned_to,
        },
        notes=f"Exception {e.id} updated",
    ))
    db.commit()

    return {"id": e.id, "status": e.status, "updated_at": e.updated_at.isoformat()}


@router.get("/summary/counts")
def exception_summary(db: Session = Depends(get_db)):
    from sqlalchemy import func
    by_status = dict(
        db.query(ExceptionRecord.status, func.count(ExceptionRecord.id))
        .group_by(ExceptionRecord.status)
        .all()
    )
    by_severity = dict(
        db.query(ExceptionRecord.severity, func.count(ExceptionRecord.id))
        .group_by(ExceptionRecord.severity)
        .all()
    )
    return {
        "total": db.query(ExceptionRecord).count(),
        "by_status": by_status,
        "by_severity": by_severity,
    }