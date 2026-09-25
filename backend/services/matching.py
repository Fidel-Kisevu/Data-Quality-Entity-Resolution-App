# Matching & reconciliation logic will live here
"""
Customer matching engine — Phase 0 spec, Section 8.

Approach:
- Blocking: group candidates by shared normalized email, phone, or name token
- Exact rules: email match (0.98), phone+lastname (0.95), email+phone (0.99)
- Fuzzy scoring: weighted combination per the spec's formula
- Thresholds: >= 0.90 probable, 0.75-0.89 possible, < 0.75 no match
- Conflict detection: for each matched group, flag disagreeing fields

Emits MatchGroup rows with record_ids, confidence, match_type, and evidence.
"""
from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime
from typing import Optional

from rapidfuzz import fuzz
from rapidfuzz.distance import JaroWinkler
from sqlalchemy.orm import Session

from models.models import Customer, MatchGroup, ExceptionRecord, AuditEvent


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------

EMAIL_NORM_RE = re.compile(r"[^a-z0-9@._%+\-]")


def norm_email(v: Optional[str]) -> Optional[str]:
    if not v:
        return None
    return v.strip().lower()


def norm_phone(v: Optional[str]) -> Optional[str]:
    if not v:
        return None
    digits = re.sub(r"\D", "", v)
    return digits or None


def norm_name(v: Optional[str]) -> Optional[str]:
    if not v:
        return None
    return v.strip().lower()


def first_token(v: Optional[str]) -> Optional[str]:
    if not v:
        return None
    parts = v.strip().split()
    return parts[0].lower() if parts else None


def last_token(v: Optional[str]) -> Optional[str]:
    if not v:
        return None
    parts = v.strip().split()
    return parts[-1].lower() if parts else None


# ---------------------------------------------------------------------------
# Sub-scores
# ---------------------------------------------------------------------------

def email_score(a: Optional[str], b: Optional[str]) -> float:
    na, nb = norm_email(a), norm_email(b)
    if not na or not nb:
        return 0.5  # neutral
    return 1.0 if na == nb else 0.0


def phone_score(a: Optional[str], b: Optional[str]) -> float:
    na, nb = norm_phone(a), norm_phone(b)
    if not na or not nb:
        return 0.5
    if na == nb:
        return 1.0
    # tolerate country-code prefix differences: 254XXXXXXXXX vs 0XXXXXXXXX
    if na.endswith(nb) or nb.endswith(na):
        return 0.9
    return 0.0


def name_score(a: Optional[str], b: Optional[str]) -> float:
    na, nb = norm_name(a), norm_name(b)
    if not na or not nb:
        return 0.5
    jw = JaroWinkler.similarity(na, nb)          # already 0.0 – 1.0
    ts = fuzz.token_sort_ratio(na, nb) / 100.0   # returns 0–100
    return max(jw, ts)


def dob_score(a, b) -> float:
    if a is None or b is None:
        return 0.5
    return 1.0 if a == b else 0.0


def city_score(a: Optional[str], b: Optional[str]) -> float:
    na, nb = norm_name(a), norm_name(b)
    if not na or not nb:
        return 0.5
    return fuzz.token_set_ratio(na, nb) / 100.0


# ---------------------------------------------------------------------------
# Composite score
# ---------------------------------------------------------------------------

def composite_score(a: Customer, b: Customer) -> dict:
    es = email_score(a.email, b.email)
    ps = phone_score(a.phone, b.phone)
    ns = name_score(a.full_name, b.full_name)
    ds = dob_score(a.date_of_birth, b.date_of_birth)
    cs = city_score(a.city, b.city)

    score = 0.35 * es + 0.25 * ps + 0.25 * ns + 0.10 * ds + 0.05 * cs

    # Strong exact-match shortcuts per Section 8.1
    if es == 1.0 and ps == 1.0:
        score = max(score, 0.99)
    elif es == 1.0:
        score = max(score, 0.98)
    elif ps == 1.0 and last_token(a.full_name) == last_token(b.full_name):
        score = max(score, 0.95)

    return {
        "score": round(score, 4),
        "signals": {
            "email": es,
            "phone": ps,
            "name": round(ns, 4),
            "dob": ds,
            "city": round(cs, 4),
        },
    }


# ---------------------------------------------------------------------------
# Blocking
# ---------------------------------------------------------------------------

def build_blocks(customers: list[Customer]) -> dict:
    """Return a dict of block_key -> list of customer ids."""
    blocks: dict[str, list[str]] = defaultdict(list)

    for c in customers:
        e = norm_email(c.email)
        if e:
            blocks[f"email:{e}"].append(c.id)

        p = norm_phone(c.phone)
        if p:
            # block on last 9 digits to normalize +254 prefix variance
            blocks[f"phone:{p[-9:]}"].append(c.id)

        lt = last_token(c.full_name)
        ft = first_token(c.full_name)
        if lt and ft:
            blocks[f"name:{lt}:{ft[0]}"].append(c.id)

    # only keep blocks with >1 candidate
    return {k: v for k, v in blocks.items() if len(v) > 1}


# ---------------------------------------------------------------------------
# Group assembly
# ---------------------------------------------------------------------------

def classify(score: float) -> str:
    if score >= 0.90:
        return "probable"
    if score >= 0.75:
        return "possible"
    return "no_match"


def detect_conflicts(records: list[Customer]) -> dict:
    """Return a dict of field -> list of distinct values, for fields that disagree."""
    conflicts = {}
    for field in ("email", "phone", "date_of_birth", "full_name", "city", "country"):
        values = {getattr(c, field) for c in records if getattr(c, field) not in (None, "")}
        if len(values) > 1:
            conflicts[field] = sorted(str(v) for v in values)
    return conflicts


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_customer_matching(db: Session) -> dict:
    """..."""
    customers = db.query(Customer).all()
    if len(customers) < 2:
        return {"groups_created": 0, "reason": "not enough customers"}

    # Clean up any previous needs_review groups (idempotent runs)
    db.query(MatchGroup).filter(MatchGroup.status == "needs_review").delete()
    db.query(ExceptionRecord).filter(ExceptionRecord.status == "new").delete()
    db.commit()

    by_id = {c.id: c for c in customers}
    blocks = build_blocks(customers)

    # ------------------------------------------------------------------
    # Phase 1: score every candidate pair, remember the best score per pair
    # ------------------------------------------------------------------
    pair_scores: dict[tuple[str, str], dict] = {}

    for block_key, member_ids in blocks.items():
        for i, id_a in enumerate(member_ids):
            for id_b in member_ids[i + 1:]:
                pair = tuple(sorted((id_a, id_b)))
                if pair in pair_scores:
                    continue

                a = by_id[id_a]
                b = by_id[id_b]

                # Skip exact same-source duplicates — those are UNIQ-01 quality findings
                if a.source_system == b.source_system and a.source_customer_id == b.source_customer_id:
                    continue

                result = composite_score(a, b)
                match_type = classify(result["score"])
                if match_type == "no_match":
                    continue

                pair_scores[pair] = {
                    "score": result["score"],
                    "match_type": match_type,
                    "signals": result["signals"],
                }

    # ------------------------------------------------------------------
    # Phase 2: union-find over matched pairs
    # ------------------------------------------------------------------
    parent: dict[str, str] = {c.id: c.id for c in customers}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for (a, b) in pair_scores:
        union(a, b)

    # ------------------------------------------------------------------
    # Phase 3: build one group per connected component
    # ------------------------------------------------------------------
    components: dict[str, list[str]] = {}
    for c in customers:
        root = find(c.id)
        components.setdefault(root, []).append(c.id)

    # Only keep components with 2+ members
    components = {k: v for k, v in components.items() if len(v) > 1}

    groups_created = 0
    groups_by_type = {"probable": 0, "possible": 0}
    exceptions_created = 0

    for root, member_ids in components.items():
        # Best score in the component = max over all pairs inside it
        best_score = 0.0
        best_signals = {}
        for i, id_a in enumerate(member_ids):
            for id_b in member_ids[i + 1:]:
                pair = tuple(sorted((id_a, id_b)))
                if pair in pair_scores:
                    if pair_scores[pair]["score"] > best_score:
                        best_score = pair_scores[pair]["score"]
                        best_signals = pair_scores[pair]["signals"]

        match_type = classify(best_score)

        records = [by_id[i] for i in member_ids]
        conflicts = detect_conflicts(records)

        group = MatchGroup(
            entity_type="customer",
            match_type=match_type,
            confidence_score=best_score,
            status="needs_review",
            proposed_surviving_id=None,
            record_ids=member_ids,
            evidence={
                "signals": best_signals,
                "conflicts": conflicts,
                "size": len(member_ids),
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(group)
        db.flush()

        groups_created += 1
        groups_by_type[match_type] = groups_by_type.get(match_type, 0) + 1

        if match_type == "possible":
            db.add(ExceptionRecord(
                exception_type="EXC-MATCH-LOW",
                severity="High",
                status="new",
                related_entity_type="customer",
                related_record_ids=member_ids,
                group_id=group.id,
                title=f"Possible match ({len(member_ids)} records)",
                description=(
                    f"Confidence {best_score:.2f} below probable threshold. "
                    f"Signals: {best_signals}"
                ),
                system_suggestion="Review side-by-side and confirm or reject",
                evidence={"signals": best_signals, "conflicts": conflicts},
            ))
            exceptions_created += 1

        if conflicts.get("date_of_birth"):
            db.add(ExceptionRecord(
                exception_type="EXC-CONFLICT",
                severity="Critical",
                status="new",
                related_entity_type="customer",
                related_record_ids=member_ids,
                group_id=group.id,
                title="DOB conflict across sources",
                description=f"Conflicting DOB values: {conflicts['date_of_birth']}",
                system_suggestion="Choose the correct value",
                evidence={"conflicts": conflicts},
            ))
            exceptions_created += 1

    # Audit
    db.add(AuditEvent(
        event_type="matching.run",
        entity_type=None,
        entity_id=None,
        actor="system",
        action="run_customer_matching",
        before_state=None,
        after_state={
            "blocks": len(blocks),
            "pairs_evaluated": len(pair_scores),
            "groups_created": groups_created,
            "groups_by_type": groups_by_type,
            "exceptions_created": exceptions_created,
        },
        notes=f"Matching produced {groups_created} consolidated groups",
    ))
    db.commit()

    return {
        "blocks": len(blocks),
        "pairs_evaluated": len(pair_scores),
        "groups_created": groups_created,
        "groups_by_type": groups_by_type,
        "exceptions_created": exceptions_created,
    }