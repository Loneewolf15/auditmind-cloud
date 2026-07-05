# AuditMind — Open Source Track
![CI](https://github.com/Loneewolf15/auditmind-oss/actions/workflows/test.yml/badge.svg)

> **"AuditMind doesn't just verify identity — it remembers verification, permanently and compliantly, powered entirely by Cognee's open-source memory engine."**

**AuditMind** is a tamper-evident AI memory layer for identity-critical systems. It sits underneath any upstream verification process (facial recognition, ID scanning, biometric checks) and turns raw pass/fail events into a permanent, queryable, and legally-forgettable audit graph — with no external database. Cognee is the sole persistence layer.

**Hackathon:** WeMakeDevs × Cognee "Where's My Context?" — June 29 to July 5, 2026
**Track:** Best Use of Cognee Open Source
**Team:** AuditMind — Divine, Success, Chukwuemelie

---

## The Problem

Upstream identity systems verify people but produce no queryable audit trail. When a regulator asks *"Was this candidate the same person throughout their exam?"* or *"Prove this KYC check happened and who authorised it"* — traditional systems have no answer. They forget.

AuditMind fixes that for three high-stakes Nigerian contexts:

1. **Exam Integrity (JAMB/CBT)** — continuous identity verification across a session, with a graph trail that can detect proxy candidates after the fact.
2. **Banking KYC (CBN Circular BSD/DIR/PUB/LAB/019/002)** — prove a customer was verified, with surgical NDPR deletion that removes one record without destroying the institutional trail.
3. **Pension Remote Verification** — replace manual field visits with a permanent, auditable digital memory of liveness checks.
4. **Traffic Identity Audit** — cross-checkpoint driver identity tracking that flags impossible travel speeds and plate mismatches.

---

## Why Cognee (Open Source)

AuditMind uses Cognee as its **sole database**. No PostgreSQL. No Redis. No external search engine. Every event is written to Cognee's self-hosted hybrid graph-vector store (KuzuDB + LanceDB) via the open-source SDK.

All four lifecycle APIs are used explicitly:

| API | How AuditMind uses it |
|-----|-----------------------|
| `cognee.remember()` | Ingests identity events as typed `DataPoint` graph entities (`IdentityEvent → SessionEntity → UserEntity → AnomalyType`) with a custom extraction prompt |
| `cognee.recall()` | `GRAPH_COMPLETION` search lets compliance officers query in natural language — *"Show all anomalies in session jamb_2026_fraud_002"* |
| `cognee.improve()` | Explicit enrichment pass after each scenario — the UI shows a Before/After comparison of agent answers to prove the graph got smarter |
| `cognee.forget()` | NDPR/GDPR Article 17 surgical deletion — wipes one session from graph + vector stores and issues a signed Certificate of Erasure |

The AI agent has **no amnesia**: memory persists across infinite browser sessions. Refreshing the page and clicking *Prove Persistent Memory* re-hydrates the D3 graph and the agent recalls every event by name — from Cognee's local stores, not the browser.

---

## Quick Start

```bash
git clone https://github.com/Loneewolf15/auditmind-oss.git
cd auditmind-oss

python3.11 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

cp .env.selfhosted.example .env.selfhosted
# Fill in your LLM_API_KEY in .env.selfhosted

make run-selfhosted
```

Open `frontend/index.html` in your browser.

---

## Demo Scenarios

No typing required — one click per scenario:

1. **Clean Exam Session** — Normal verification chain. Green nodes. Clean graph.
2. **Fraud Attempt** — Confidence degrades mid-session. Red anomaly nodes cluster. Agent detects the proxy candidate.
3. **NDPR Purge Request** — Nodes fade out. `cognee.forget()` wipes the dataset. A signed certificate of deletion is issued.
4. **Traffic Identity Audit** — Driver A001 passes two tollgates cleanly, hits an impossible-speed anomaly at Sagamu, then a plate mismatch at Ibadan.

After any scenario: click **Prove Persistent Memory** — refresh the page first if you want to make the point viscerally.

---

## Architecture

```
Browser (D3.js + Tailwind)
        │  fetch()
        ▼
FastAPI Backend
        │  cognee.remember() / recall() / improve() / forget()
        ▼
Cognee Open Source SDK
        ├── KuzuDB  (graph: entities + relationships)
        └── LanceDB (vector: semantic search index)
```

---

## Judging Criteria

| Criterion | Evidence |
|-----------|----------|
| **Best Use of Cognee** | All 4 lifecycle APIs, custom `DataPoint` schema, `GRAPH_COMPLETION` search, self-hosted only |
| **Potential Impact** | Real Nigerian regulatory context (NDPR, JAMB, CBN) |
| **Creativity** | `forget()` as a legal compliance tool with a certificate of erasure |
| **Technical Excellence** | 32 passing tests, GitHub Actions CI, Dockerized, Railway-ready |
| **User Experience** | One-click scenarios, live D3 graph, Before/After improve() comparison |

---

## Stack

Python 3.11 · FastAPI · Cognee SDK (KuzuDB + LanceDB) · Anthropic Claude · Google Gemini (fallback) · D3.js · Tailwind CSS · Docker · Railway

---

## Disclosure

AI assistants (Claude) were used during development in compliance with hackathon Rule 8. All creative direction, architecture decisions, and implementation were by the team.
