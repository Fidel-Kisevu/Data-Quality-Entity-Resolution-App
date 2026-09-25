# DataQ — Portfolio Notes

Talking points for interviews, LinkedIn, and GitHub README highlights.

---

## Elevator Pitch

> "I built DataQ — an end-to-end data quality and reconciliation platform. It ingests messy customer data from multiple sources, runs 22 quality rules, matches duplicates using fuzzy algorithms, resolves conflicts through rule-based survivorship, and exposes a trusted dataset with full lineage — plus an AI Analyst that answers questions using only trusted data, and an immutable audit trail of every decision."

---

## The Story Arc

**1. Specification-first, not code-first**
I started by locking the scope: a Phase 0 Specification Pack with personas, user journeys, data schemas, quality rules, matching thresholds, exception workflows, ML scope, evaluation metrics, and acceptance criteria. Only then did I write code.

**2. Rule-based baseline before ML**
The spec's principle was "strong non-ML baseline first, then ML where it clearly adds value." I implemented all 22 rules as transparent, testable queries. ML becomes a measurable upgrade, not an opaque shortcut.

**3. Empirical iteration over speculation**
When the engine over-fired (895 findings), I diagnosed by inspecting the actual data — not by guessing. When matching returned 441 pairwise groups instead of ~188 consolidated ones, I traced it to the missing union-find step. Every fix was grounded in measurement.

**4. Full pipeline, not a demo fragment**
Ingest → quality → match → reconcile → trust → ask → audit. All six journeys work end-to-end. All decisions are logged.

---

## What to Highlight in Interviews

### On design decisions

> "I used union-find to consolidate match groups. Without it, one person appearing in three sources generates three pairwise groups. With it, they collapse into one 3-member group — much cleaner for the reconciliation UI, and it aligns with how a data steward actually thinks about a 'person'."

### On troubleshooting

> "When the quality engine produced 895 findings on the first run, I suspected either over-firing rules or duplicated groups. I wrote a diagnostic script that dumped every finding by rule and cross-referenced against the injected issues file. Turned out two problems: the CONS rules fired per-record instead of per-group, and UNIQ-02 was flagging all cross-source matches — which is actually a *matching* concern, not a quality problem. I patched both rules, and the count dropped to 252."

### On why audit trails matter

> "The value proposition is 'trusted and audit-ready data.' Without an immutable audit trail, 'trusted' is just a claim. Every state transition — upload, ingest, quality run, match, resolve, AI query — writes an audit event before commit. You can trace any trusted record back through every decision that produced it."

### On the AI Analyst

> "The spec required the AI Analyst to answer only from trusted data and never hallucinate. I built a rule-based stub — no LLM — that reads only the trusted store, returns the exact metric that produced the answer, and refuses to answer when it can't ground the response. Swapping in an LLM later is a 20-line change: the same context gets passed, the same grounding contract applies."

### On the tradeoffs

> "I chose SQLite for MVP. The schema is PostgreSQL-compatible and everything would port cleanly. I chose not to build the frontend beyond the shell because the value of the product is in the pipeline, and Swagger is a legitimate interface for a data platform at MVP. The frontend becomes a natural next step, not a blocker."

---

## Numbers to Quote

- **22 quality rules** implemented across 5 dimensions
- **521 raw customers**, **458 transactions** across 4 sources
- **188 consolidated match groups** (union-find, no pairwise duplication)
- **313 duplicates** linked to survivors
- **252 quality findings** across 42 Critical / 124 High / 86 Medium
- **17 audit events** across 6 event types
- **100% audit completeness** — every state change logged

---

## GitHub README Hook

```
DataQ — turns messy multi-source data into trusted, explainable, audit-ready information.

22 quality rules · fuzzy entity matching · transitive consolidation · rule-based survivorship · grounded AI analyst · immutable audit trail

Built from a locked Phase 0 spec. All six journeys work end-to-end.
```

---

## LinkedIn / Blog Post Angles

1. **"Why we lock the spec before writing code"** — Phase 0 as a defensive engineering practice
2. **"Rule-based before ML: a case for the unglamorous baseline"** — why the spec's sequencing matters
3. **"Union-find for entity resolution"** — a specific algorithm story with concrete numbers
4. **"Building an audit-first data pipeline"** — why every state change writes before commit
5. **"When over-firing is a metric problem, not a bug"** — the 895→252 investigation

---

## Questions to Ask Interviewers

- How do you balance rule-based logic with ML in your data quality stack?
- What's your current approach to entity resolution — blocking strategy, scoring, thresholds?
- How do you store and query audit trails at scale?
- How do you prevent "trusted data" from becoming a black box?