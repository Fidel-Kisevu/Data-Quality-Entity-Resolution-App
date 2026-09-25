# DataQ — Phase 0 Specification Pack

**Version:** 0.2  
**Status:** Locked (Decisions Confirmed)  
**Date:** 2026-09-24  
**Author:** Project Team  

---

## 1. Document Control

| Item              | Detail                                      |
|-------------------|---------------------------------------------|
| Document Title    | DataQ – Phase 0 Specification Pack   |
| Related Documents | Project Statement & Master Build Blueprint  |
| Purpose           | Lock MVP scope, user journeys, data model, quality rules, matching logic, exceptions, ML scope, evaluation, and acceptance criteria before implementation begins |

---

## 2. Product Summary

**One-sentence statement**  
DataQ is an intelligent data quality, reconciliation and analytics platform that ingests multi-source data, detects structural and semantic quality issues, identifies duplicates and anomalies, reconciles conflicts, and surfaces uncertain cases for human verification — producing trusted, explainable and audit-ready data.

**Core value proposition**  
Turns messy multi-source data into trusted, explainable and audit-ready information.

**Primary user**  
Data Steward / Data Quality Analyst (person responsible for making data reliable)

**Secondary user**  
Business Analyst / Auditor (person who consumes trusted data or needs to understand decisions)

**MVP Goal**  
A working system that can:
- Ingest 2–3 simulated source files
- Detect a defined set of quality issues and duplicates
- Present conflicts for human reconciliation
- Produce a trusted output dataset
- Maintain a full audit trail of every decision
- Answer basic questions via an AI Analyst that only uses trusted data

**Out of Scope for MVP**
- Real-time streaming ingestion
- Direct database connectors (file upload only)
- Advanced ML model training UI
- Multi-tenant / role-based access beyond single Steward role
- Production-grade scalability
- Automated remediation (system only suggests; human decides)
- Complex multi-level approval workflows

---

## 3. User Personas & Goals

### Primary Persona – Data Steward (Alex)
- **Goal:** Make multi-source data trustworthy with minimum manual effort
- **Pain:** Spends hours finding duplicates, fixing inconsistencies, and defending data decisions
- **Success looks like:** Clear quality scores, easy comparison of conflicting records, fast resolution, and a complete audit log

### Secondary Persona – Analyst / Auditor (Jordan)
- **Goal:** Trust the numbers and understand how they were produced
- **Pain:** Doesn’t know whether a figure came from source A or B, or whether it was manually overridden
- **Success looks like:** Ability to see the trusted dataset, ask questions, and drill into the audit trail of any record

---

## 4. MVP User Journeys

### Journey 1 – Ingest Data
1. User lands on Data Sources page
2. Uploads 2–3 CSV/Excel files (or selects sample datasets)
3. System validates file structure and shows preview + basic profiling
4. User confirms mapping to canonical entities
5. System stores raw files and creates ingestion job  
**Success:** Files accepted, job status visible, raw data preserved

### Journey 2 – Run Quality Assessment
1. User selects one or more datasets and clicks “Run Quality Check”
2. System executes rule-based + basic statistical checks
3. Results appear on Quality Findings Dashboard
4. User can filter and drill into individual findings  
**Success:** All defined rules executed, findings stored with severity and evidence

### Journey 3 – Review & Resolve Duplicates / Conflicts
1. User opens Reconciliation Workspace
2. System shows candidate duplicate/conflict groups with side-by-side comparison
3. User reviews differences, chooses surviving record or merges values
4. User confirms decision → system records the action in audit log and updates trusted store  
**Success:** Conflict resolved, trusted record updated, full decision history kept

### Journey 4 – Handle Exceptions
1. Cases the system cannot resolve automatically appear in Exception Queue
2. User opens an exception, sees evidence and suggested action
3. User resolves, rejects, or escalates
4. Decision is logged  
**Success:** Exception moves to terminal state with complete audit entry

### Journey 5 – Consume Trusted Data + AI Analyst
1. User views Trusted Data table or exports it
2. User opens AI Analyst and asks a question
3. System answers only from trusted data and cites sources/decisions when relevant  
**Success:** Answer is correct, grounded, and explainable

### Journey 6 – Audit Trail
1. User searches for a record or time period
2. System shows every transformation, quality flag, model suggestion, and human decision  
**Success:** Complete, immutable history available

---

## 5. Screen-by-Screen UI Requirements

### 5.1 Login / Home
**Purpose:** Simple entry point and overview of system status.  
**Key components:** Login form, summary cards (Total Sources, Open Exceptions, Last Quality Run, Trusted Records), quick actions, recent activity feed.  
**Acceptance criteria:** User can log in and immediately see system health; one-click access to key actions.

### 5.2 Data Sources / Upload
**Purpose:** Ingest new data.  
**Key components:** Source list, drag-and-drop upload, file preview, column mapping, “Confirm & Ingest” button, job status.  
**Acceptance criteria:** User can upload, preview, map, and ingest files; raw files preserved.

### 5.3 Dataset Overview
**Purpose:** High-level view of a single dataset.  
**Key components:** Name, source, row count, profiling summary, quality score, action buttons.  
**Acceptance criteria:** Current state understood in seconds; clear next actions.

### 5.4 Quality Findings Dashboard
**Purpose:** Show all detected quality issues.  
**Key components:** Severity cards, breakdown by issue type, filterable findings table, drill-down.  
**Acceptance criteria:** All rules produce findings with evidence; filtering and drill-down work.

### 5.5 Record Detail / Comparison View
**Purpose:** Inspect or compare records side-by-side.  
**Key components:** Side-by-side comparison, highlighted differences, source badges, action panel (Keep A / Keep B / Merge / Exception).  
**Acceptance criteria:** Differences obvious; resolution possible in few clicks; decision audited.

### 5.6 Reconciliation Workspace
**Purpose:** Main area for resolving duplicates and conflicts.  
**Key components:** Candidate groups list, filters, confidence scores, progress indicator, link to comparison view.  
**Acceptance criteria:** User can work through all open groups; resolved groups update trusted store.

### 5.7 Exception Queue
**Purpose:** Handle cases requiring human judgment.  
**Key components:** Filterable list, detail panel, status workflow, resolution actions.  
**Acceptance criteria:** All automatic failures land here; full decision history recorded.

### 5.8 Trusted Data View
**Purpose:** Show clean, reconciled output.  
**Key components:** Trusted records table, search/filter, lineage link, export.  
**Acceptance criteria:** Only clean records appear; full lineage available; export works.

### 5.9 AI Analyst
**Purpose:** Answer questions using only trusted data.  
**Key components:** Chat interface, suggested questions, grounded answers with citations, refusal when data insufficient.  
**Acceptance criteria:** Answers factually correct and grounded; clear limitations stated.

### 5.10 Audit Trail / Reports
**Purpose:** Full transparency and defensibility.  
**Key components:** Search by record/date/user/action, timeline view, export.  
**Acceptance criteria:** Every significant action recorded with timestamp, actor, and before/after values.

**Navigation (MVP):** Left sidebar – Home, Data Sources, Quality Findings, Reconciliation, Exceptions, Trusted Data, AI Analyst, Audit Trail.

---

## 6. Data Specification

### 6.1 Simulated Source Systems

| Source ID | Name                  | Typical Content                     | Arrival Method |
|-----------|-----------------------|-------------------------------------|----------------|
| SRC-CRM   | CRM System            | Customer master data                | CSV upload     |
| SRC-ERP   | ERP / Billing System  | Customers + Transactions            | CSV upload     |
| SRC-MKT   | Marketing / Support   | Customer list + interaction data    | Excel upload   |

### 6.2 Canonical / Trusted Schema

#### Customer
| Field                | Type          | Required | Description                              |
|----------------------|---------------|----------|------------------------------------------|
| customer_id          | string (UUID) | Yes      | System-generated trusted ID              |
| source_customer_ids  | array         | Yes      | Original IDs from each source            |
| full_name            | string        | Yes      | Standardized full name                   |
| first_name           | string        | No       |                                          |
| last_name            | string        | No       |                                          |
| email                | string        | No       | Primary email                            |
| phone                | string        | No       | Primary phone (E.164 preferred)          |
| date_of_birth        | date          | No       |                                          |
| address_line1        | string        | No       |                                          |
| city                 | string        | No       |                                          |
| country              | string        | No       | ISO country code preferred               |
| status               | string        | Yes      | active / inactive / unknown              |
| created_at           | timestamp     | Yes      |                                          |
| updated_at           | timestamp     | Yes      |                                          |
| confidence_score     | float         | No       | 0–1 after matching                       |
| is_manually_reviewed | boolean       | Yes      |                                          |

#### Transaction
| Field                   | Type          | Required | Description                              |
|-------------------------|---------------|----------|------------------------------------------|
| transaction_id          | string (UUID) | Yes      | System-generated trusted ID              |
| source_transaction_ids  | array         | Yes      | Original IDs from sources                |
| customer_id             | string        | Yes      | Link to trusted Customer                 |
| transaction_date        | date          | Yes      |                                          |
| amount                  | decimal       | Yes      |                                          |
| currency                | string        | Yes      | ISO currency code                        |
| description             | string        | No       |                                          |
| status                  | string        | Yes      | completed / pending / refunded / disputed|
| source_system           | string        | Yes      |                                          |
| created_at              | timestamp     | Yes      |                                          |
| updated_at              | timestamp     | Yes      |                                          |

### 6.3 Sample Datasets & Deliberate Problems

**Volumes (MVP):**  
- CRM: ~180–220 customers  
- ERP: ~150 customers + ~400–500 transactions  
- Marketing: ~200 customers  

**Injected problem categories:**
- Completeness (missing email/phone/DOB/amount/date)
- Validity / Format (bad emails, phones, dates, currencies)
- Uniqueness (exact and near duplicates within and across sources)
- Consistency / Conflicts (different email, phone, DOB, amount for same entity)
- Anomalies (extreme amounts, future dates, implausible ages)
- Semantic challenges (name variations, typos, married names)

**Deliverables:** Three source files + ground-truth mapping file + data dictionary of injected issues.

---

## 7. Data Quality Framework

### 7.1 Quality Dimensions
Completeness, Validity, Uniqueness, Consistency, Accuracy, Timeliness.

### 7.2 Severity Levels
| Severity  | Meaning                                              | Typical Action                  |
|-----------|------------------------------------------------------|---------------------------------|
| Critical  | Blocks trust / major failure                         | Must review before Trusted      |
| High      | Strongly reduces confidence                          | High priority in queues         |
| Medium    | Notable but usable                                   | Visible; user decides           |
| Low       | Minor / cosmetic                                     | Logged, low visibility          |
| Info      | Observation only                                     | No action required              |

### 7.3 Concrete Quality Rules (MVP)

**Completeness**
- COMP-01: Missing full name → Critical
- COMP-02: Missing both email and phone → High
- COMP-03: Missing email → Medium
- COMP-04: Missing amount → Critical
- COMP-05: Missing transaction date → Critical
- COMP-06: Missing currency → High

**Validity**
- VAL-01: Invalid email format → High
- VAL-02: Invalid phone format → Medium
- VAL-03: Invalid / future / too-old DOB → High
- VAL-04: Invalid amount (≤0 or extreme) → High
- VAL-05: Invalid currency code → High
- VAL-06: Future transaction date → High

**Uniqueness**
- UNIQ-01: Exact duplicate within source → High
- UNIQ-02: Exact duplicate across sources → High
- UNIQ-03: Potential duplicate transaction → Medium

**Consistency**
- CONS-01: Conflicting email across sources → High
- CONS-02: Conflicting phone across sources → High
- CONS-03: Conflicting date of birth → Critical
- CONS-04: Name variation beyond threshold → Medium
- CONS-05: Amount conflict on matched transaction → Critical

**Anomaly**
- ANOM-01: Extreme amount outlier → Medium
- ANOM-02: Implausible age → High

Findings contain rule_id, entity/record IDs, severity, evidence, status, and timestamp. Critical/High findings block automatic entry into Trusted store.

---

## 8. Reconciliation & Matching Rules

### 8.1 Customer Matching
**Blocking:** Shared normalized email, phone, or strong name tokens.

**Exact rules:**
- Exact normalized email → Exact Match (0.98)
- Exact normalized phone + same last name → Exact Match (0.95)
- Exact email + exact phone → Exact Match (0.99)

**Fuzzy scoring features:** Email similarity, phone match, name fuzzy scores, DOB match, address/city (lower weight).

**Thresholds:**
- ≥ 0.90 → Probable Match
- 0.75–0.89 → Possible Match (human review)
- < 0.75 → No Match

### 8.2 Transaction Matching
- Same customer + exact amount + exact date → Exact (0.97)
- Same customer + exact amount + date ±1 day → Probable (0.88)
- Same customer + amount within 1% + exact date → Possible (0.80)

### 8.3 Conflict Detection
Matched records that disagree on important fields (email, phone, DOB, amount, status, etc.) generate conflicts.

### 8.4 Survivorship (applied in order)
1. **Source priority (locked):** ERP > CRM > Marketing
2. Most recent value (when timestamps exist)
3. Prefer non-null over null
4. Human override always wins
5. Field-level preferences (e.g. most complete name)

### 8.5 Exception Triggers
- Possible Match range
- Critical conflicts
- Unresolvable survivorship
- Anomaly flags
- Previous user rejection of suggestion

---

## 9. Exception Management

### 9.1 Exception Types
| Code            | Trigger                                      | Default Severity |
|-----------------|----------------------------------------------|------------------|
| EXC-MATCH-LOW   | Low-confidence match                         | High             |
| EXC-CONFLICT    | Critical field conflict                      | Critical         |
| EXC-SURVIVE     | Unresolvable survivorship                    | High             |
| EXC-ANOMALY     | Anomaly detected                             | Medium/High      |
| EXC-QUALITY     | Open Critical quality findings               | Critical         |
| EXC-MANUAL      | User escalation                              | High             |
| EXC-DUP         | Ambiguous duplicate group                    | High             |

### 9.2 States
`New → In Review → Resolved / Rejected / Escalated`

### 9.3 Required Fields
exception_id, type, severity, status, related entity/records, title, description, system_suggestion, evidence, timestamps, actors, resolution_decision, resolution_notes.

### 9.4 Resolution Actions
Accept suggestion / Manual override / Keep separate / Reject match / Mark reviewed.  
Every action writes an immutable audit event.

---

## 10. ML / AI Specification (MVP)

### Principles
- Strong non-ML baseline first
- ML only where it clearly improves results
- All predictions explainable and overridable
- AI Analyst uses **only** trusted data

### ML Scope
| Problem                  | Approach                                      |
|--------------------------|-----------------------------------------------|
| Customer Matching        | Fuzzy features + simple classifier / ranking  |
| Transaction Matching     | Mostly rules + light scoring                  |
| Anomaly Detection        | Statistical + Isolation Forest / z-score      |
| Survivorship             | Rule-based only                               |
| AI Analyst               | LLM grounded on trusted data only             |

### AI Analyst Constraints
- Answers only from Trusted store
- Must not hallucinate numbers
- Must refuse or qualify when data is insufficient
- Logs every question and answer

### Explicitly Out of Scope for MVP
End-to-end deep learning entity resolution, auto-retraining pipelines, complex ensembles, querying raw data with the AI Analyst.

---

## 11. Evaluation Plan

### Key Metrics & Targets

**Data Quality Detection**
- Rule Recall ≥ 95%
- Rule Precision ≥ 90%
- Critical Capture Rate = 100%
- False Positive Rate ≤ 5%

**Customer Matching**
- Precision (Probable+Exact) ≥ 95%
- Recall ≥ 85%
- F1 ≥ 0.90
- False Merge Rate ≤ 1%

**Anomaly Detection**
- Injected Anomaly Recall ≥ 80%
- False Positive Rate ≤ 8%

**Exceptions & Audit**
- Exception Precision ≥ 85%
- Audit Completeness = 100%

**AI Analyst**
- Factual Accuracy ≥ 95%
- Grounding Rate = 100%
- Proper refusal when data insufficient ≥ 90%

**Process**
1. Measure pure rule-based baseline
2. Measure ML-enhanced version
3. Document lift
4. Version datasets and results

---

## 12. API Surface (MVP)

**Auth:** `POST /auth/login`, `POST /auth/logout`  

**Ingestion:** `POST /sources/upload`, `GET /sources`, `GET /sources/{id}`, `POST /sources/{id}/ingest`  

**Quality:** `POST /quality/run`, `GET /quality/findings`, `GET /quality/findings/{id}`  

**Reconciliation:** `GET /reconciliation/groups`, `GET /reconciliation/groups/{id}`, `POST /reconciliation/groups/{id}/resolve`  

**Exceptions:** `GET /exceptions`, `GET /exceptions/{id}`, `PATCH /exceptions/{id}`  

**Trusted Data:** `GET /trusted/customers`, `GET /trusted/transactions`, `GET /trusted/customers/{id}`, `GET /trusted/export`  

**AI Analyst:** `POST /ai/query`  

**Audit:** `GET /audit`, `GET /audit/record/{id}`  

All state-changing endpoints write audit events.

---

## 13. System States & Business Rules

**Record states:** Raw → Profiled → Quality Checked → Matching → In Review → Trusted → Archived

**Key Business Rules**
1. Records with open Critical findings cannot enter Trusted store
2. Every change to a trusted record creates an immutable audit event
3. Human decisions always override system suggestions
4. AI Analyst may only read from Trusted store
5. Source raw data is never modified
6. Match groups and exceptions remain queryable after resolution

---

## 14. Acceptance Criteria & Definition of Done

**Phase 0 Done when:**
- All sections of this document are reviewed and locked
- Sample dataset + ground-truth design is complete
- No blocking open questions remain

**MVP Done when:**
- All six user journeys work end-to-end
- All listed screens meet their acceptance criteria
- Quality rules, matching, exceptions, and audit trail function as specified
- Evaluation metrics are measured and documented (baseline + ML)
- AI Analyst is grounded and accurate
- README, architecture diagrams, evaluation results, and screenshots are portfolio-ready

---

## 15. Locked Decisions, Assumptions & Remaining Questions

### Locked Decisions (2026-09-24)

| Decision                    | Choice                                                                 |
|----------------------------|------------------------------------------------------------------------|
| Source priority order      | **ERP > CRM > Marketing**                                              |
| Role-based access (MVP)    | **Steward-only** (single role)                                         |
| Backend                    | Python + FastAPI + SQLite (MVP) → PostgreSQL later                     |
| Frontend                   | React + Vite + Tailwind                                                |
| Data / ML libraries        | pandas, scikit-learn, rapidfuzz                                        |
| AI Analyst                 | OpenAI or Anthropic API with strict “trusted data only” grounding      |

### Assumptions
- File upload only in MVP
- English-only data and UI
- Sample volumes remain in the low hundreds / low thousands of rows
- No complex multi-user concurrent editing required for MVP

### Remaining Open Question
- **Industry flavour for sample data** — Still open.  
  Options: Generic / E-commerce / SaaS subscriptions / Healthcare / Finance / Insurance.  
  Recommendation: Keep **Generic (or light E-commerce / SaaS)** unless you have a strong preference. It keeps the data easy to understand for portfolio reviewers.

---

## 16. Confirmed Tech Stack (MVP)

| Layer          | Choice                                      | Notes                                      |
|----------------|---------------------------------------------|--------------------------------------------|
| Backend        | Python 3.11+ / FastAPI                      |                                            |
| Database       | SQLite (MVP) → PostgreSQL later             | SQLAlchemy ORM                             |
| Frontend       | React + Vite + Tailwind CSS                 |                                            |
| Data handling  | pandas                                      |                                            |
| Fuzzy matching | rapidfuzz                                   |                                            |
| ML             | scikit-learn                                | Matching classifier + anomaly detection    |
| AI Analyst     | OpenAI or Anthropic API                     | Strict system prompt + trusted-data only   |
| Auth (MVP)     | Simple login (single Steward user)          | Can be expanded later                      |

---

**End of Phase 0 Specification Pack (v0.2 – Locked)**

**Next recommended step:**  
Generate the concrete sample datasets + ground-truth file + injected issues dictionary, then begin project skeleton + data layer.
