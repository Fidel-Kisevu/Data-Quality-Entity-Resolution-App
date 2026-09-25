"""
Survivorship rules — Phase 0 spec, Section 8.4.

Priority order:
1. Source priority: ERP > CRM > MKT
2. Most recent value (if timestamps exist)
3. Non-null over null
4. Human override always wins
5. Field-level preference (most complete name, etc.)
"""
from __future__ import annotations

from typing import Optional
from sqlalchemy.orm import Session

from models.models import Customer
from core.config import get_settings

settings = get_settings()
SOURCE_PRIORITY = settings.SOURCE_PRIORITY  # ["ERP", "CRM", "MKT"]


def _source_rank(source_system: Optional[str]) -> int:
    """Lower index = higher priority."""
    try:
        return SOURCE_PRIORITY.index(source_system or "")
    except ValueError:
        return 99


def pick_surviving_record(records: list[Customer]) -> Customer:
    """
    Choose the record that 'wins' for the group.
    Priority: source rank, then most recently updated.
    """
    return sorted(
        records,
        key=lambda c: (_source_rank(c.source_system), -(c.updated_at.timestamp() if c.updated_at else 0)),
    )[0]


def build_survivorship_values(records: list[Customer]) -> dict:
    """
    For each field, pick the winning value using the priority rules.
    Returns a dict {field: value}.
    """
    fields = [
        "full_name", "first_name", "last_name",
        "email", "phone", "date_of_birth",
        "address_line1", "city", "country", "status",
    ]
    surviving = pick_surviving_record(records)

    result = {}
    for field in fields:
        # 1. human override wins — not implemented in MVP storage yet; skip
        # 2. try the surviving record first
        value = getattr(surviving, field, None)
        if value not in (None, ""):
            result[field] = value
            continue
        # 3. otherwise, prefer non-null from the highest-priority non-surviving record
        ordered = sorted(records, key=lambda c: _source_rank(c.source_system))
        for r in ordered:
            v = getattr(r, field, None)
            if v not in (None, ""):
                result[field] = v
                break
        else:
            result[field] = None

    return {
        "surviving_record_id": surviving.id,
        "surviving_source": surviving.source_system,
        "values": result,
    }