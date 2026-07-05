from fastapi import FastAPI, HTTPException, Request, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import time
import os
import logging

logger = logging.getLogger(__name__)

# Import local modules
from .models import EventIngestRequest, QueryRequest, ForgetReasonRequest, ChatRequest
from . import cloud_sync
from .scenarios import get_scenarios
from . import cognee_service

# --- API Key Auth ---
# Set AUDITMIND_API_KEY env var to enable auth on destructive endpoints.
# If unset, auth is skipped (for local dev without env config).
_API_KEY = os.getenv("AUDITMIND_API_KEY", "")

async def require_api_key(x_api_key: Optional[str] = Header(None)):
    if _API_KEY and x_api_key != _API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key header")

app = FastAPI(
    title="AuditMind AI Memory Layer",
    description="Tamper-evident AI memory layer for identity-critical systems powered by Cognee",
    version="1.0.0"
)

# Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error_code": "VALIDATION_ERROR", "message": str(exc.errors())},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    error_str = str(exc)
    if "RetryError" in error_str or "tenacity" in str(type(exc)).lower() or "timeout" in error_str.lower():
        message = "Cognee service unavailable after multiple retries. Request failed."
    else:
        # Do not leak internal error details (stack traces, DB messages, file paths)
        message = "An internal error occurred. Please try again."

    return JSONResponse(
        status_code=500,
        content={"error_code": "SERVER_ERROR", "message": message},
    )

# Latency Middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(f"{request.method} {request.url.path} completed in {process_time:.4f}s")
    return response

# Enable CORS for the frontend.
# Add your production URL here before deploying, e.g. "https://auditmind.vercel.app"
_extra = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
    "null",  # file:// — opening index.html directly from disk
] + _extra

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "auditmind-backend"}

@app.post("/api/event")
async def ingest_event(request: EventIngestRequest):
    event_dict = request.model_dump()
    result = await cognee_service.remember_event(event_dict)
    return result

@app.post("/api/query")
async def audit_query(request: QueryRequest):
    result = await cognee_service.recall_audit(request.query, request.session_id)
    return result

@app.post("/api/improve/{session_id}")
async def improve_graph(session_id: str):
    result = await cognee_service.improve_session(session_id)
    return result

@app.delete("/api/forget", dependencies=[Depends(require_api_key)])
async def forget_data(session_id: str, request: ForgetReasonRequest):
    result = await cognee_service.forget_session(session_id, request.reason)
    return result

@app.get("/api/scenarios")
async def scenarios_endpoint():
    return get_scenarios()

@app.get("/api/graph/nodes")
async def get_graph_nodes():
    """
    Returns all cached events as D3-compatible nodes and links.
    Used to re-hydrate the frontend graph after a page refresh.
    The underlying data lives in Cognee's KuzuDB and survives both
    page refreshes and backend restarts.
    """
    all_data = cognee_service.get_all_cached_event_data()
    nodes = []
    links = []
    seen_sessions: set = set()
    seen_users: set = set()

    for session_id, events in all_data.items():
        if session_id not in seen_sessions:
            nodes.append({"id": session_id, "label": f"Session: {session_id}", "type": "session"})
            seen_sessions.add(session_id)

        for event in events:
            user_id = event.get("user_id", "unknown")
            event_id = event.get("event_id", "unknown")
            confidence = event.get("confidence", 1.0)
            event_type = event.get("event_type", "unknown")

            status = "CLEAN"
            if confidence < 0.5:
                status = "HIGH_RISK"
            elif confidence < 0.7:
                status = "ANOMALY"

            if user_id not in seen_users:
                nodes.append({"id": user_id, "label": f"User: {user_id}", "type": "user"})
                links.append({"source": user_id, "target": session_id, "type": "started"})
                seen_users.add(user_id)

            nodes.append({
                "id": event_id,
                "label": event_type,
                "type": "event",
                "status": status,
                "session": session_id,
            })
            links.append({"source": session_id, "target": event_id, "type": "has_event"})

    return {"nodes": nodes, "links": links, "sessions": list(all_data.keys())}


@app.get("/api/graph/export")
async def export_graph(session_id: Optional[str] = None):
    path = await cognee_service.export_graph(session_id)
    return {"status": "success", "path": path}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    The AI agent endpoint. Cognee recalls relevant graph memory, Claude reasons over it.
    This is the 'no amnesia' story: memory persists across infinite sessions.
    """
    history = [m.model_dump() for m in (request.history or [])]
    result = await cognee_service.agent_chat(request.message, request.session_id, history)
    return result

@app.get("/api/mode")
async def get_mode():
    """
    Returns the current Cognee backend mode for the UI indicator.
    Self-hosted (Open Source prize) vs Cloud (Cloud prize).
    Also reports whether cloud sync is available.
    """
    graph_db = os.getenv("GRAPH_DATABASE_PROVIDER", "kuzu")
    vector_db = os.getenv("VECTOR_DB_PROVIDER", "lancedb")
    llm_model = os.getenv("LLM_MODEL", "claude-haiku-4-5-20251001")
    agent_model = os.getenv("AGENT_LLM_MODEL", "claude-sonnet-4-6")
    is_cloud = os.getenv("COGNEE_API_KEY") is not None or graph_db not in ("kuzu", "networkx", "neo4j", "falkordb")
    return {
        "mode": "cloud" if is_cloud else "self-hosted",
        "graph_db": graph_db,
        "vector_db": vector_db,
        "llm_model": llm_model,
        "agent_model": agent_model,
        "cloud_sync_available": cloud_sync.cloud_configured(),
        "cached_sessions": cognee_service.get_all_cached_sessions(),
    }

@app.post("/api/sync")
async def sync_to_cloud(session_id: Optional[str] = None):
    """
    Sync locally stored audit events to Cognee Cloud.
    Runs add_text + cognify against the cloud tenant.
    If session_id is provided, syncs only that session.
    If omitted, syncs all cached sessions.
    """
    if not cloud_sync.cloud_configured():
        raise HTTPException(
            status_code=503,
            detail="Cognee Cloud is not configured. Set COGNEE_CLOUD_BASE_URL, COGNEE_CLOUD_API_KEY, and COGNEE_CLOUD_TENANT_ID in .env"
        )

    if session_id:
        sessions_to_sync = [session_id]
    else:
        sessions_to_sync = cognee_service.get_all_cached_sessions()

    if not sessions_to_sync:
        raise HTTPException(
            status_code=400,
            detail="No events cached locally. Run a scenario first to ingest events, then sync."
        )

    results = []
    for sid in sessions_to_sync:
        events = cognee_service.get_cached_events(sid)
        if not events:
            results.append({"session_id": sid, "status": "skipped", "reason": "no cached events"})
            continue
        try:
            result = await cloud_sync.sync_session_to_cloud(f"session_{sid}", events)
            result["session_id"] = sid
            results.append(result)
            logger.info(f"Synced session {sid} to Cognee Cloud ({len(events)} events)")
        except Exception as e:
            logger.error(f"Cloud sync failed for session {sid}: {e}")
            results.append({"session_id": sid, "status": "failed", "error": str(e)})

    synced = sum(1 for r in results if r.get("status") == "synced")
    return {
        "status": "complete",
        "sessions_synced": synced,
        "sessions_total": len(sessions_to_sync),
        "results": results,
        "cloud_url": os.getenv("COGNEE_CLOUD_BASE_URL", ""),
        "tenant_id": os.getenv("COGNEE_CLOUD_TENANT_ID", ""),
    }
