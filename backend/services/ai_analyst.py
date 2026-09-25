"""
AI Analyst — Phase 0 spec, Section 5.9 & Section 10.

STUB implementation — no LLM. Answers common questions using only the
Trusted Data store. Constrained to:
- Refuse when data is insufficient
- Never invent numbers
- Return the same shape we'd expect from a real LLM-backed Analyst

Rule categories handled:
- Counts: "how many customers/transactions?"
- Averages/sums: "average amount", "total amount"
- Top-N: "top 5 cities", "top cities"
- By-source: "how many from CRM?"
- By-status: "how many active customers?"
- Refusal fallback for anything else

Swap-in later: replace _answer() with an LLM call that receives the same
trusted-data context.
"""
from __future__ import annotations

import re
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session

from models.models import Customer, Transaction, AuditEvent


def _record_audit(db: Session, question: str, answer: str, matched_rule: str) -> None:
    db.add(AuditEvent(
        event_type="ai.query",
        entity_type=None,
        entity_id=None,
        actor="user",
        action="ask_ai_analyst",
        before_state=None,
        after_state={"question": question, "answer": answer, "matched_rule": matched_rule},
        notes=f"AI Analyst answered via rule '{matched_rule}'",
    ))
    db.commit()


def _trusted_customer_query(db: Session):
    return db.query(Customer).filter(Customer.is_trusted == True)


def _trusted_transaction_query(db: Session):
    trusted_ids = [row[0] for row in db.query(Customer.id).filter(Customer.is_trusted == True).all()]
    if not trusted_ids:
        return db.query(Transaction).filter(False)
    return db.query(Transaction).filter(Transaction.customer_id.in_(trusted_ids))


def _answer(db: Session, question: str) -> dict:
    q = question.lower().strip()

    # ---- Customers: how many ----
    if "how many customer" in q or "number of customer" in q:
        n = _trusted_customer_query(db).count()
        return {
            "answer": f"There are {n} trusted customer records.",
            "evidence": {"metric": "trusted_customer_count", "value": n},
            "matched_rule": "count_customers",
        }

    # ---- Transactions: how many ----
    if "how many transaction" in q or "number of transaction" in q:
        n = _trusted_transaction_query(db).count()
        return {
            "answer": f"There are {n} transactions linked to trusted customers.",
            "evidence": {"metric": "trusted_transaction_count", "value": n},
            "matched_rule": "count_transactions",
        }

    # ---- Top-N cities ----
    m = re.search(r"top\s+(\d+)?\s*cit", q)
    if m or "top cities" in q or "which cities" in q:
        top_n = int(m.group(1)) if m and m.group(1) else 5
        rows = (
            _trusted_customer_query(db)
            .with_entities(Customer.city, func.count(Customer.id).label("n"))
            .filter(Customer.city.isnot(None))
            .group_by(Customer.city)
            .order_by(func.count(Customer.id).desc())
            .limit(top_n)
            .all()
        )
        if not rows:
            return {
                "answer": "No city data available in the trusted store.",
                "evidence": {},
                "matched_rule": "refuse_no_data",
            }
        summary = ", ".join(f"{city} ({n})" for city, n in rows)
        return {
            "answer": f"Top {len(rows)} cities by trusted customers: {summary}.",
            "evidence": {"metric": f"top_{top_n}_cities", "rows": rows},
            "matched_rule": "top_cities",
        }

    # ---- Average transaction amount ----
    if "average" in q and ("amount" in q or "transaction" in q or "value" in q):
        avg = _trusted_transaction_query(db).with_entities(func.avg(Transaction.amount)).scalar()
        if avg is None:
            return {
                "answer": "No transactions in the trusted store to average.",
                "evidence": {},
                "matched_rule": "refuse_no_data",
            }
        return {
            "answer": f"The average transaction amount is {float(avg):,.2f}.",
            "evidence": {"metric": "avg_transaction_amount", "value": float(avg)},
            "matched_rule": "avg_transaction_amount",
        }

    # ---- Sum transaction amount ----
    if "total" in q and ("amount" in q or "transaction" in q or "value" in q):
        total = _trusted_transaction_query(db).with_entities(func.sum(Transaction.amount)).scalar()
        if total is None:
            return {
                "answer": "No transactions in the trusted store to sum.",
                "evidence": {},
                "matched_rule": "refuse_no_data",
            }
        return {
            "answer": f"The total transaction amount is {float(total):,.2f}.",
            "evidence": {"metric": "sum_transaction_amount", "value": float(total)},
            "matched_rule": "sum_transaction_amount",
        }

    # ---- By source ----
    if "from crm" in q or "from erp" in q or "from marketing" in q or "from mkt" in q:
        source = None
        for s in ("CRM", "ERP", "MKT"):
            if s.lower() in q or ("marketing" in q and s == "MKT"):
                source = s
                break
        if source:
            n = _trusted_customer_query(db).filter(Customer.source_system == source).count()
            return {
                "answer": f"{n} trusted customers came from {source}.",
                "evidence": {"metric": "count_by_source", "source": source, "value": n},
                "matched_rule": "count_by_source",
            }

    # ---- By status ----
    for status in ("active", "inactive", "unknown"):
        if status in q:
            n = _trusted_customer_query(db).filter(Customer.status == status).count()
            return {
                "answer": f"There are {n} trusted customers with status '{status}'.",
                "evidence": {"metric": "count_by_status", "status": status, "value": n},
                "matched_rule": "count_by_status",
            }

    # ---- Refusal ----
    return {
        "answer": (
            "I can only answer questions about counts, averages, totals, "
            "top cities, source breakdowns, and statuses — using the trusted "
            "data store only. Please rephrase."
        ),
        "evidence": {"hint": "Try: 'how many customers?', 'top 5 cities', 'average transaction amount'"},
        "matched_rule": "refuse_unrecognized",
    }


def ask(db: Session, question: str) -> dict:
    """Public entry: answer a question using trusted data only."""
    started = datetime.utcnow()
    result = _answer(db, question)
    elapsed_ms = int((datetime.utcnow() - started).total_seconds() * 1000)

    _record_audit(db, question, result["answer"], result["matched_rule"])

    return {
        "question": question,
        "answer": result["answer"],
        "evidence": result["evidence"],
        "matched_rule": result["matched_rule"],
        "grounded": True,
        "latency_ms": elapsed_ms,
    }