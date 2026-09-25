"""
Ingestion service.

Responsibilities:
- Detect file type (CSV / Excel)
- Parse into a pandas DataFrame
- Normalize column names
- Insert rows into Customer or Transaction tables
- Compute a basic profile (per-column null counts, dtypes, unique counts, samples)
- Write an audit event for the ingestion
"""
from __future__ import annotations

import json
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional, Any

import pandas as pd
from sqlalchemy.orm import Session

from models.models import Source, Customer, Transaction, AuditEvent


# ---------------------------------------------------------------------------
# Column normalization
# ---------------------------------------------------------------------------

# Maps many possible incoming column names → canonical field names
CUSTOMER_COLUMN_MAP = {
    "customer_id": "source_customer_id",
    "cust_id": "source_customer_id",
    "id": "source_customer_id",
    "full_name": "full_name",
    "name": "full_name",
    "first_name": "first_name",
    "fname": "first_name",
    "last_name": "last_name",
    "lname": "last_name",
    "surname": "last_name",
    "email": "email",
    "email_address": "email",
    "phone": "phone",
    "phone_number": "phone",
    "mobile": "phone",
    "date_of_birth": "date_of_birth",
    "dob": "date_of_birth",
    "birth_date": "date_of_birth",
    "address_line1": "address_line1",
    "address": "address_line1",
    "city": "city",
    "country": "country",
    "status": "status",
}

TRANSACTION_COLUMN_MAP = {
    "transaction_id": "source_transaction_id",
    "txn_id": "source_transaction_id",
    "id": "source_transaction_id",
    "customer_id": "source_customer_id",
    "cust_id": "source_customer_id",
    "transaction_date": "transaction_date",
    "txn_date": "transaction_date",
    "date": "transaction_date",
    "amount": "amount",
    "value": "amount",
    "currency": "currency",
    "description": "description",
    "status": "status",
}


def _normalize_columns(df: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    """Rename columns to canonical names based on the mapping (case-insensitive)."""
    rename = {}
    for col in df.columns:
        key = str(col).strip().lower().replace(" ", "_")
        if key in mapping:
            rename[col] = mapping[key]
    return df.rename(columns=rename)


# ---------------------------------------------------------------------------
# Type coercion helpers
# ---------------------------------------------------------------------------

def _to_date(value: Any) -> Optional[date]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        ts = pd.to_datetime(value, errors="coerce")
        if pd.isna(ts):
            return None
        return ts.date()
    except Exception:
        return None


def _to_decimal(value: Any) -> Optional[Decimal]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return None


def _to_str(value: Any) -> Optional[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = str(value).strip()
    return s if s else None


# ---------------------------------------------------------------------------
# Entity-type detection
# ---------------------------------------------------------------------------

def detect_entity_type(source_system: str, filename: str) -> str:
    """
    Decide whether a file contains customers or transactions.
    - ERP files with 'transaction' or 'txn' in the name → transaction
    - Everything else → customer
    """
    name = filename.lower()
    if "transaction" in name or "txn" in name:
        return "transaction"
    if source_system == "ERP" and "transaction" in name:
        return "transaction"
    return "customer"


# ---------------------------------------------------------------------------
# Main ingestion
# ---------------------------------------------------------------------------

def ingest_source(db: Session, source: Source) -> dict:
    """
    Parse the stored file for `source`, insert rows into Customer or Transaction,
    compute a profile, and write an audit event.

    Returns a summary dict.
    """
    if not source.stored_path:
        raise ValueError("Source has no stored_path — upload may have failed")

    path = Path(source.stored_path)
    if not path.exists():
        raise FileNotFoundError(f"Stored file missing: {path}")

    # 1. Read file
    if path.suffix.lower() in (".xlsx", ".xls"):
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)

    if df.empty:
        raise ValueError("Uploaded file is empty")

    # 2. Normalize columns
    entity_type = detect_entity_type(source.source_system, source.original_filename)
    if entity_type == "customer":
        df = _normalize_columns(df, CUSTOMER_COLUMN_MAP)
    else:
        df = _normalize_columns(df, TRANSACTION_COLUMN_MAP)

    # 3. Compute profile BEFORE inserting (so we profile the raw file)
    profile = _profile_dataframe(df)

    # 4. Insert rows
    inserted = 0
    if entity_type == "customer":
        inserted = _insert_customers(db, df, source)
    else:
        inserted = _insert_transactions(db, df, source)

    # 5. Update Source
    source.row_count = inserted
    source.profile_json = profile
    source.status = "profiled"
    source.updated_at = datetime.utcnow()

    # 6. Audit event
    db.add(AuditEvent(
        event_type="source.ingested",
        entity_type="source",
        entity_id=source.id,
        actor="system",
        action="ingest",
        before_state={"status": "raw", "row_count": None},
        after_state={
            "status": "profiled",
            "row_count": inserted,
            "entity_type": entity_type,
            "columns": list(df.columns),
        },
        notes=f"Ingested {inserted} {entity_type} rows from {source.original_filename}",
    ))

    db.commit()
    db.refresh(source)

    return {
        "source_id": source.id,
        "entity_type": entity_type,
        "rows_inserted": inserted,
        "columns": list(df.columns),
        "profile": profile,
    }


# ---------------------------------------------------------------------------
# Row insertion
# ---------------------------------------------------------------------------

def _insert_customers(db: Session, df: pd.DataFrame, source: Source) -> int:
    count = 0
    for _, row in df.iterrows():
        customer = Customer(
            source_id=source.id,
            source_system=source.source_system,
            source_customer_id=_to_str(row.get("source_customer_id")),
            full_name=_to_str(row.get("full_name")),
            first_name=_to_str(row.get("first_name")),
            last_name=_to_str(row.get("last_name")),
            email=_to_str(row.get("email")),
            phone=_to_str(row.get("phone")),
            date_of_birth=_to_date(row.get("date_of_birth")),
            address_line1=_to_str(row.get("address_line1")),
            city=_to_str(row.get("city")),
            country=_to_str(row.get("country")),
            status=_to_str(row.get("status")) or "unknown",
            is_trusted=False,
            is_manually_reviewed=False,
        )
        db.add(customer)
        count += 1
    return count


def _insert_transactions(db: Session, df: pd.DataFrame, source: Source) -> int:
    count = 0
    for _, row in df.iterrows():
        txn = Transaction(
            source_id=source.id,
            source_system=source.source_system,
            source_transaction_id=_to_str(row.get("source_transaction_id")),
            source_customer_id=_to_str(row.get("source_customer_id")),   # ← NEW
            customer_id=None,  # resolved later by transaction_linker
            transaction_date=_to_date(row.get("transaction_date")),
            amount=_to_decimal(row.get("amount")),
            currency=_to_str(row.get("currency")),
            description=_to_str(row.get("description")),
            status=_to_str(row.get("status")) or "completed",
            is_trusted=False,
        )
        db.add(txn)
        count += 1
    return count

# ---------------------------------------------------------------------------
# Profiling
# ---------------------------------------------------------------------------

def _profile_dataframe(df: pd.DataFrame) -> dict:
    """Return per-column profile: dtype, nulls, unique count, sample values."""
    profile = {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "columns": {},
    }
    for col in df.columns:
        series = df[col]
        null_count = int(series.isna().sum())
        profile["columns"][col] = {
            "dtype": str(series.dtype),
            "null_count": null_count,
            "null_pct": round(null_count / len(df) * 100, 2) if len(df) else 0.0,
            "unique_count": int(series.nunique(dropna=True)),
            "sample_values": [str(v) for v in series.dropna().head(3).tolist()],
        }
    return profile