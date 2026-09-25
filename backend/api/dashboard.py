from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from core.database import get_db
from models.models import (
    Source, Customer, Transaction, MatchGroup, ExceptionRecord,
    QualityFinding, AuditEvent,
)

router = APIRouter()


@router.get("/stats")
def dashboard_stats(db: Session = Depends(get_db)):
    """
    Single endpoint returning all Home-page KPIs.
    Everything is computed from real data — no hardcoding.
    """
    # Sources
    total_sources = db.query(Source).count()
    profiled_sources = db.query(Source).filter(Source.status == "profiled").count()

    # Customers & transactions (raw)
    total_customers = db.query(Customer).count()
    total_transactions = db.query(Transaction).count()
    linked_transactions = db.query(Transaction).filter(
        Transaction.customer_id.isnot(None)
    ).count()

    # Trusted
    trusted_customers = db.query(Customer).filter(Customer.is_trusted == True).count()
    duplicates_linked = db.query(Customer).filter(
        Customer.trusted_customer_id.isnot(None),
        Customer.is_trusted == False,
    ).count()

    # Match groups
    total_groups = db.query(MatchGroup).count()
    resolved_groups = db.query(MatchGroup).filter(MatchGroup.status == "resolved").count()
    open_groups = db.query(MatchGroup).filter(MatchGroup.status == "needs_review").count()

    # Findings
    total_findings = db.query(QualityFinding).filter(QualityFinding.status == "open").count()
    critical_findings = db.query(QualityFinding).filter(
        QualityFinding.status == "open",
        QualityFinding.severity == "Critical",
    ).count()

    # Exceptions
    total_exceptions = db.query(ExceptionRecord).count()
    open_exceptions = db.query(ExceptionRecord).filter(
        ExceptionRecord.status == "new"
    ).count()
    critical_exceptions = db.query(ExceptionRecord).filter(
        ExceptionRecord.status == "new",
        ExceptionRecord.severity == "Critical",
    ).count()

    # Audit
    total_audit_events = db.query(AuditEvent).count()

    # Derived KPIs
    match_health_pct = (
        round(100 * resolved_groups / total_groups, 1) if total_groups else 0.0
    )
    transaction_coverage_pct = (
        round(100 * linked_transactions / total_transactions, 1)
        if total_transactions else 0.0
    )

    # Risk score — simple heuristic
    # Critical items push it up; healthy pipelines pull it down.
    risk_points = critical_findings * 2 + critical_exceptions * 3 + open_exceptions
    if risk_points == 0:
        risk_level = "Low"
    elif risk_points < 20:
        risk_level = "Low"
    elif risk_points < 60:
        risk_level = "Medium"
    else:
        risk_level = "High"

    return {
        "sources": {
            "total": total_sources,
            "profiled": profiled_sources,
        },
        "customers": {
            "raw": total_customers,
            "trusted": trusted_customers,
            "duplicates_linked": duplicates_linked,
        },
        "transactions": {
            "total": total_transactions,
            "linked": linked_transactions,
            "coverage_pct": transaction_coverage_pct,
        },
        "matching": {
            "total_groups": total_groups,
            "resolved": resolved_groups,
            "open": open_groups,
            "health_pct": match_health_pct,
        },
        "quality": {
            "total_findings": total_findings,
            "critical_findings": critical_findings,
        },
        "exceptions": {
            "total": total_exceptions,
            "open": open_exceptions,
            "critical_open": critical_exceptions,
        },
        "audit": {
            "total_events": total_audit_events,
        },
        "risk": {
            "level": risk_level,
            "points": risk_points,
        },
    }