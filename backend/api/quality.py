from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from core.database import get_db
from models.models import QualityFinding
from services.quality_engine import run_quality_checks

router = APIRouter()


@router.post("/run")
def run_checks(db: Session = Depends(get_db)):
    """Execute all quality rules and persist findings."""
    return run_quality_checks(db)


@router.get("/findings")
def list_findings(
    severity: Optional[str] = Query(None),
    rule_id: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    status: Optional[str] = Query("open"),
    limit: int = Query(200, le=2000),
    db: Session = Depends(get_db),
):
    q = db.query(QualityFinding)
    if severity:
        q = q.filter(QualityFinding.severity == severity)
    if rule_id:
        q = q.filter(QualityFinding.rule_id == rule_id)
    if entity_type:
        q = q.filter(QualityFinding.entity_type == entity_type)
    if status:
        q = q.filter(QualityFinding.status == status)

    total = q.count()
    rows = q.order_by(QualityFinding.created_at.desc()).limit(limit).all()

    return {
        "total": total,
        "returned": len(rows),
        "findings": [
            {
                "id": f.id,
                "rule_id": f.rule_id,
                "entity_type": f.entity_type,
                "record_id": f.record_id,
                "severity": f.severity,
                "message": f.message,
                "evidence": f.evidence,
                "status": f.status,
                "created_at": f.created_at.isoformat() if f.created_at else None,
            }
            for f in rows
        ],
    }


@router.get("/findings/{finding_id}")
def get_finding(finding_id: str, db: Session = Depends(get_db)):
    f = db.query(QualityFinding).filter(QualityFinding.id == finding_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Finding not found")
    return {
        "id": f.id,
        "rule_id": f.rule_id,
        "entity_type": f.entity_type,
        "record_id": f.record_id,
        "severity": f.severity,
        "message": f.message,
        "evidence": f.evidence,
        "status": f.status,
        "created_at": f.created_at.isoformat() if f.created_at else None,
    }


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    """Counts by severity, rule, and entity type."""
    by_severity = dict(
        db.query(QualityFinding.severity, func.count(QualityFinding.id))
        .filter(QualityFinding.status == "open")
        .group_by(QualityFinding.severity)
        .all()
    )
    by_rule = dict(
        db.query(QualityFinding.rule_id, func.count(QualityFinding.id))
        .filter(QualityFinding.status == "open")
        .group_by(QualityFinding.rule_id)
        .all()
    )
    by_entity = dict(
        db.query(QualityFinding.entity_type, func.count(QualityFinding.id))
        .filter(QualityFinding.status == "open")
        .group_by(QualityFinding.entity_type)
        .all()
    )
    total = db.query(QualityFinding).filter(QualityFinding.status == "open").count()

    return {
        "total_open_findings": total,
        "by_severity": by_severity,
        "by_rule": by_rule,
        "by_entity_type": by_entity,
    }