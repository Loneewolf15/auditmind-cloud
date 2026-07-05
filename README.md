# AuditMind
![CI](https://github.com/we-make-devs/auditmind/actions/workflows/test.yml/badge.svg)

> **"AuditMind doesn't verify identity — it remembers verification, permanently and compliantly, for any system that needs an audit trail."**

**AuditMind** is the audit memory layer that sits underneath any system that needs to prove who was verified, when, and with what confidence — and needs to be able to forget that record on legal request. It is built natively on Cognee's hybrid graph-vector memory engine.

**Hackathon:** WeMakeDevs × Cognee "Where's My Context?" — June 29 to July 5, 2026  
**Team:** AuditMind (Divine, Sister, Cofounder)

## The Core Problem
Upstream systems (like facial recognition engines or ID scanners) verify people, but they lack a native, queryable memory of those events. We designed AuditMind for three concrete domains where preserving the *record* of verification is critical:

1. **Exam Integrity (JAMB/CBT centres)** — proving a candidate was continuously the same person throughout a session, with a queryable graph trail if fraud is suspected afterward.
2. **Banking/Fintech KYC** — proving a customer was verified per CBN circulars, with the surgical ability to honour an NDPR deletion request without destroying the rest of the institutional audit trail.
3. **Pension Verification** — proving a pensioner is alive and was checked remotely, replacing manual field agent visits with a permanent, auditable digital memory.

AuditMind receives events (pass/fail/anomaly) from these upstream verification processes and turns them into a permanent, queryable, and legally-forgettable audit graph.

## How it works (Best Use of Cognee)
We use Cognee's core APIs (v1.0) explicitly:
1. `remember()`: Ingests structured `DataPoint` models (User, Session, Event, Anomaly) using custom graph models.
2. `recall()`: Uses `GRAPH_COMPLETION` to allow compliance officers to query memory using natural language traversing complex relationships.
3. `improve()`: explicitly triggers an enrichment pass to bridge session-level context into the permanent graph.
4. `forget()`: Our NDPR/GDPR compliance mechanism. Surgically removes a session's dataset from relational, graph, and vector stores without affecting the rest of the audit trail.
5. `visualize_graph()`: Used to render the Cognee graph live.

## Quick Start
AuditMind runs natively with zero external server dependencies using LanceDB (vector) and Kuzu (graph).

```bash
# 1. Clone repo
git clone https://github.com/.../auditmind.git
cd auditmind

# 2. Setup environment
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# 3. Run Self-Hosted Mode (MacBook Neo Track)
make run-selfhosted

# OR Run Cloud Mode (iPhone 17 Track)
make run-cloud
```

Open `frontend/index.html` in your browser to interact with the demo.

## Demo Scenarios
No typing required. Just click the pre-built scenarios in the UI:
1. **Clean Exam Session**: Normal verification sequence. Graph builds a clean chain.
2. **Fraud Attempt**: Confidence degrades. Anomaly nodes cluster visibly.
3. **NDPR Purge Request**: Legal deletion. Dataset wiped from graph and vector stores via `cognee.forget()`.

## Judging Criteria Mapping
- **Potential Impact**: Built for real-world identity verification using actual Nigerian context (NDPR, JAMB fraud stats).
- **Creativity**: Re-framing `forget()` as a legal compliance tool (NDPR/GDPR Article 17).
- **Technical Excellence**: 15 tests, GitHub Actions CI, Dockerized, cleanly separated backend/frontend.
- **Best Use of Cognee**: Uses custom `DataPoint` models, all 4 lifecycle APIs, and `visualize_graph()`.
- **User Experience**: One-click visual scenarios via D3.js + Tailwind.

## Acknowledgements & Disclosures

**AI Assistance:** Claude (Anthropic) was used during the pre-hackathon 
planning phase (before June 29, 2026) for strategic architecture decisions, 
API research, judging criteria analysis, and sprint planning. All code, 
implementation decisions, and creative direction were executed by the 
development team during the hackathon window (June 29 – July 5, 2026), 
in full compliance with Rule 8 and Rule 9.

**Stack:** Python 3.11, FastAPI, Cognee SDK, D3.js, Tailwind CSS, 
pytest, httpx, python-dotenv, uvicorn, Docker.

**Open source assets:** None. All UI and code is original work.
