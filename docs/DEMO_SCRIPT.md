# DataQ — 3-Minute Demo Script

For screen recording, live presentations, or portfolio walkthroughs.

**Setup before recording:**
- Backend running on `http://localhost:8000`
- Swagger open in browser at `/docs`
- Second tab: `http://localhost:8000/trusted/export` (for CSV demo)
- Terminal open at repo root

---

## 0:00 – 0:20 — The Problem

> "Data quality is a quiet crisis. Companies have customer data spread across CRM, ERP, and marketing systems. Records disagree. Duplicates hide. Decisions aren't documented. DataQ fixes this — and proves it, with an audit trail."

**Screen:** Show the DataQ logo in the Dashboard, or the Swagger UI title.

---

## 0:20 – 0:45 — Ingest (Journey 1)

> "We start with four sources: CRM customers, ERP customers, ERP transactions, and a marketing Excel file — 979 rows total, deliberately full of quality problems."

**Action:** In Swagger, `POST /sources/upload` → show the response with `stored_path` and `bytes_received`.

> "The file is saved to disk and registered. Now we ingest it — parse, normalize columns, insert rows, and compute a profile."

**Action:** `POST /sources/{id}/ingest` → show the response with `rows_inserted: 189` and the profile.

---

## 0:45 – 1:10 — Quality Assessment (Journey 2)

> "22 rules run across five dimensions: completeness, validity, uniqueness, consistency, anomaly."

**Action:** `POST /quality/run` → show `252 findings created`.

> "Critical, high, medium severities. Each finding points at a specific record with evidence."

**Action:** `GET /quality/summary` → show counts by severity and rule.

> "For example, VAL-03 caught 14 future-dated DOBs, ANOM-02 caught 14 implausible ages, CONS-03 flagged 18 cross-source DOB conflicts."

---

## 1:10 – 1:45 — Matching & Reconciliation (Journey 3)

> "Now the interesting part. We match customer records across sources using fuzzy logic — email, phone, name with Jaro-Winkler and Token Sort, DOB, city."

**Action:** `POST /reconciliation/run` → show `188 groups created`.

> "Union-find collapses pairwise matches into single multi-member groups. So instead of 3 groups for a person appearing in CRM + ERP + MKT, we get one group with 3 records."

**Action:** `GET /reconciliation/groups` → show first group with 3 record IDs.

> "For each group, the system suggests a survivor based on source priority — ERP wins over CRM wins over Marketing."

**Action:** `GET /reconciliation/groups/{id}` → show side-by-side comparison + `survivorship_suggestion`.

---

## 1:45 – 2:10 — Trusted Data (Journey 5)

> "One bulk action resolves all 188 groups — survivors marked trusted, duplicates linked for lineage."

**Action:** `POST /reconciliation/resolve-all` → show `188 survivors, 313 duplicates linked`.

> "The trusted store now has 188 clean customer records. Each one knows where it came from."

**Action:** `GET /trusted/customers` → show first customer with lineage array.

> "Two CRM+ERP+MKT records, one survivor, full provenance."

---

## 2:10 – 2:35 — AI Analyst (Journey 5b)

> "The AI Analyst answers questions using only trusted data. No hallucination possible."

**Action:** `POST /ai/query` with `{"question": "how many customers?"}` → show response.

> "188 — grounded, cited, audited."

**Action:** `POST /ai/query` with `{"question": "top 5 cities"}` → show response.

> "And when it can't ground the answer…"

**Action:** `POST /ai/query` with `{"question": "what is the meaning of life?"}` → show refusal.

> "…it says so. That's the difference between a chatbot and a data analyst."

---

## 2:35 – 2:55 — Audit Trail (Journey 6)

> "Every state change is logged — uploads, ingests, quality runs, matching, resolutions, AI queries."

**Action:** `GET /audit/summary` → show counts by event type.

> "17 events, 6 types, 100% completeness. Any trusted record can be traced back through every decision that produced it."

**Action:** `GET /audit/record/{customer_id}` → show the full timeline.

---

## 2:55 – 3:00 — Close

> "Ingest. Quality. Match. Reconcile. Trust. Ask. Audit. All six journeys, end-to-end, from a locked spec to a working MVP."

**Screen:** GitHub repo README with the architecture diagram.

---

## Recording Tips

- **Zoom in** on Swagger responses — the numbers are the punchline
- **Move fast** between endpoints — the story is the pipeline, not the individual clicks
- **Highlight the number changes**: 979 rows → 252 findings → 188 groups → 188 trusted
- **End on the refusal** — it demonstrates constraint, which is more impressive than capability
- **Keep it under 3 minutes** — portfolio attention spans are short

---

## Screenshot List (for README / blog)

1. `Dashboard` — frontend shell with sidebar
2. `POST /quality/run` response — 252 findings
3. `GET /reconciliation/groups/{id}` — side-by-side view with survivorship
4. `GET /trusted/customers` — first customer with 3-source lineage
5. `POST /ai/query` — grounded answer
6. `POST /ai/query` — refusal
7. `GET /audit/summary` — event type breakdown
8. Architecture diagram (rendered Mermaid)