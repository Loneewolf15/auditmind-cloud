# AuditMind — Cognee Cloud Track
![CI](https://github.com/Loneewolf15/auditmind-cloud/actions/workflows/test.yml/badge.svg)

> **"AuditMind gives compliance officers a shared, cross-machine AI memory for identity audit — powered entirely by Cognee Cloud."**

**AuditMind** is a tamper-evident AI memory layer for identity-critical systems. It ingests verification events from upstream systems (facial recognition, ID scanners, biometric checks), stores them in a Cognee Cloud tenant as a queryable knowledge graph, and lets compliance officers anywhere in the world ask natural language questions about what happened, who was involved, and whether anything was suspicious.

**Hackathon:** WeMakeDevs × Cognee "Where's My Context?" — June 29 to July 5, 2026
**Track:** Best Use of Cognee Cloud
**Team:** AuditMind — Divine, Success, Chukwuemelie

---

## The Problem

Identity verification systems verify people but produce no queryable, cross-machine audit trail. A compliance officer on a different machine, in a different office, has no way to query what happened in a session last week. The AI agent forgets the moment the session ends.

AuditMind fixes that — powered by Cognee Cloud, which means the audit memory is available anywhere, on any machine, forever.

---

## Use Cases

1. **Exam Integrity (JAMB/CBT)** — detect proxy candidates across distributed exam centres, with a cloud-backed graph that survives machine restarts.
2. **Banking KYC (CBN Circular BSD/DIR/PUB/LAB/019/002)** — prove customer verification across branches, with cross-machine NDPR Article 17 deletion.
3. **Pension Remote Verification** — cloud audit trail of liveness checks across field teams.
4. **Traffic Identity Audit** — cross-checkpoint driver tracking with cloud-persisted anomaly detection.

---

## Why Cognee Cloud

AuditMind uses Cognee Cloud as its **sole persistence layer**. Events ingested locally are synced to the cloud tenant via Cognee's API, making the audit graph available to any compliance officer with the frontend URL — no local database required on their machine.

| API / Feature | How AuditMind uses it |
|---------------|-----------------------|
| `add_text` + `cognify` | Syncs formatted audit events to the Cognee Cloud knowledge graph |
| `cognee.recall()` — `GRAPH_COMPLETION` | Natural language compliance queries traversing the cloud graph |
| `cognee.improve()` | Enrichment pass — Before/After comparison shows the cloud graph getting smarter |
| `cognee.forget()` (cloud) | Cross-machine NDPR/GDPR Article 17 deletion — removes dataset from the cloud tenant and issues a Certificate of Erasure |
| Mode badge | UI dynamically reports `Cognee Cloud · persistent across machines` |

The killer demo: one compliance officer ingests a fraud scenario and syncs to cloud. A second officer on a completely different machine opens the frontend, clicks **Prove Persistent Memory**, and the agent recalls every flagged event by name — from Cognee Cloud, not local state.

---

## Quick Start

```bash
git clone https://github.com/Loneewolf15/auditmind-cloud.git
cd auditmind-cloud

python3.11 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

cp .env.cloud.example .env.cloud
# Fill in COGNEE_CLOUD_BASE_URL, COGNEE_CLOUD_API_KEY, COGNEE_CLOUD_TENANT_ID

make run-cloud
```

Open `frontend/index.html` in your browser.

---

## Demo Scenarios

1. **Clean Exam Session** — Events stored in Cognee Cloud. Agent answers compliance questions from cloud memory.
2. **Fraud Attempt** — Anomaly nodes stored in cloud. Query *"Was there fraud in session jamb_2026_fraud_002?"* — agent cites specific event IDs and confidence scores.
3. **NDPR Purge Request** — Cloud dataset deleted. Certificate of Erasure issued. Agent confirms: *"I have no record of this session — data was erased under NDPR Article 17."*
4. **Traffic Identity Audit** — Driver identity tracked across checkpoints in cloud graph. Plate mismatch surfaced by natural language query.

After any scenario, click **Sync to Cognee Cloud** then **Prove Persistent Memory** to demonstrate cross-machine persistence.

---

## Architecture

```
Browser (D3.js + Tailwind)
        │  fetch()
        ▼
FastAPI Backend
        │  cognee.remember() locally → /api/sync → Cognee Cloud
        │  cognee.recall() via GRAPH_COMPLETION
        │  cognee.improve() / forget()
        ▼
Cognee Cloud Tenant
        ├── Cloud Graph Store  (entities + relationships)
        └── Cloud Vector Store (semantic search index)
```

---

## Judging Criteria

| Criterion | Evidence |
|-----------|----------|
| **Best Use of Cognee Cloud** | Cloud tenant as sole DB, `add_text` + `cognify` sync, cloud `forget()`, cross-machine persistence demo |
| **Potential Impact** | Real Nigerian regulatory context (NDPR, JAMB, CBN) at enterprise scale |
| **Creativity** | Cloud `forget()` as a legal compliance tool — NDPR Article 17 across machines |
| **Technical Excellence** | 32 passing tests, GitHub Actions CI, Dockerized, Railway-ready |
| **User Experience** | One-click scenarios, live D3 graph, Sync to Cloud button, Before/After improve() comparison |

---

## Stack

Python 3.11 · FastAPI · Cognee Cloud API · Anthropic Claude · Google Gemini (fallback) · D3.js · Tailwind CSS · Docker · Railway

---

## Disclosure

AI assistants (Claude) were used during development in compliance with hackathon Rule 8. All creative direction, architecture decisions, and implementation were by the team.
