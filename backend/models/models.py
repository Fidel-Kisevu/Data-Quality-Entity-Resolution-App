from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    String, Text, Boolean, Float, DateTime, Date, Numeric,
    ForeignKey, JSON, Integer
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base
import uuid


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    source_system: Mapped[str] = mapped_column(String(20), nullable=False)  # CRM / ERP / MKT
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="raw")  # raw / profiled / quality_checked / reconciled
    row_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    stored_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    profile_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    source_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("sources.id"), nullable=True)
    source_customer_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source_system: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    address_line1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="unknown")

    # Trusted record fields
    is_trusted: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_manually_reviewed: Mapped[bool] = mapped_column(Boolean, default=False)
    trusted_customer_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)  # links to surviving record

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    source_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("sources.id"), nullable=True)
    source_transaction_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source_system: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    source_customer_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)   
    customer_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("customers.id"), nullable=True)

    transaction_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="completed")

    is_trusted: Mapped[bool] = mapped_column(Boolean, default=False)
    trusted_transaction_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    


class QualityFinding(Base):
    __tablename__ = "quality_findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    rule_id: Mapped[str] = mapped_column(String(20), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(30), nullable=False)  # customer / transaction
    record_id: Mapped[str] = mapped_column(String(36), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="open")  # open / resolved / ignored
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MatchGroup(Base):
    __tablename__ = "match_groups"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    entity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    match_type: Mapped[str] = mapped_column(String(30), nullable=False)  # exact / probable / possible
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="needs_review")  # needs_review / resolved / exception
    proposed_surviving_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    record_ids: Mapped[dict] = mapped_column(JSON, nullable=False)  # list of record IDs
    evidence: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ExceptionRecord(Base):
    __tablename__ = "exceptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    exception_type: Mapped[str] = mapped_column(String(30), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="new")  # new / in_review / resolved / rejected / escalated
    related_entity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    related_record_ids: Mapped[dict] = mapped_column(JSON, nullable=False)
    group_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    system_suggestion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    resolution_decision: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assigned_to: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    actor: Mapped[str] = mapped_column(String(100), nullable=False)  # "system" or user
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    before_state: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    after_state: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
