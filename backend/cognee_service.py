import cognee
from cognee.low_level import DataPoint
from .graph_models import IdentityEvent, IDENTITY_EXTRACTION_PROMPT
from datetime import datetime, timedelta
import json
import os
from tenacity import retry, stop_after_attempt, wait_fixed
import logging
from cognee.modules.search.types.SearchType import SearchType

logger = logging.getLogger(__name__)

# In-memory event cache: session_id → list of formatted text strings.
# Populated on every remember_event() call. Used by the cloud sync endpoint
# to replay events to Cognee Cloud without requiring a second DB query.
_event_cache: dict[str, list[str]] = {}

# Structured event data cache: session_id → list of raw event dicts.
# Used by /api/graph/nodes to re-hydrate the D3 graph after a page refresh.
# Memory in Cognee's KuzuDB survives both page refreshes and backend restarts;
# this cache mirrors that for fast graph reconstruction without a Cognee query.
_event_data_cache: dict[str, list[dict]] = {}


def get_cached_events(session_id: str) -> list[str]:
    return _event_cache.get(session_id, [])


def get_all_cached_sessions() -> list[str]:
    return list(_event_cache.keys())


def get_all_cached_event_data() -> dict[str, list[dict]]:
    return _event_data_cache


AGENT_SYSTEM_PROMPT = """You are AuditMind, a compliance AI agent with persistent memory powered by Cognee's hybrid graph-vector memory engine.

Your memory contains identity verification events from:
- Exam integrity sessions (JAMB/CBT centres across Nigeria)
- KYC verifications (per CBN Circular BSD/DIR/PUB/LAB/019/002)
- Pension remote verification sessions

When answering:
- Ground every answer in the memory context retrieved from the Cognee graph
- If context is empty or irrelevant, say explicitly: "I have no memory of this"
- Cite specific event IDs, session IDs, confidence scores, and flags when available
- Flag risk levels clearly: HIGH_RISK (confidence < 0.5), ANOMALY (0.5–0.7), CLEAN (> 0.7)
- Reference NDPR 2019 / GDPR Article 17 when deletion or erasure is discussed
- If a dataset was purged, confirm: "I have no record of [user/session] — this data was erased under NDPR Article 17"

You demonstrate that AI agents do not need to suffer from amnesia. Cognee gives you permanent, queryable memory across infinite sessions."""

@retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
async def remember_event(event_data: dict) -> dict:
    """
    Stores one identity event as a typed graph entity.
    Uses permanent memory mode (no session_id) for audit trail durability.
    Also caches the formatted text for cloud sync.
    """
    text = format_event_as_text(event_data)
    dataset_name = f"session_{event_data['session_id']}"

    # Cache for cloud sync — keeps the formatted text per session
    session_id = event_data['session_id']
    if session_id not in _event_cache:
        _event_cache[session_id] = []
    _event_cache[session_id].append(text)

    # Cache raw event dict for graph re-hydration after page refresh
    if session_id not in _event_data_cache:
        _event_data_cache[session_id] = []
    _event_data_cache[session_id].append(event_data)

    result = await cognee.remember(
        text,
        dataset_name=dataset_name,
        graph_model=IdentityEvent,
        custom_prompt=IDENTITY_EXTRACTION_PROMPT,
        self_improvement=True,
    )
    return {
        "status": result.status if hasattr(result, 'status') else "success",
        "dataset": result.dataset_name if hasattr(result, 'dataset_name') else dataset_name,
        "elapsed": result.elapsed_seconds if hasattr(result, 'elapsed_seconds') else 0,
    }


async def recall_audit(query: str, session_id: str = None) -> dict:
    """
    Queries audit memory. Uses GRAPH_COMPLETION for relationship traversal.
    Optionally session-aware for compliance officer workflows.
    """
    datasets = [f"session_{session_id}"] if session_id else None
    
    results = await cognee.recall(
        query_text=query,
        datasets=datasets,
        session_id="compliance_officer",
        query_type=SearchType.GRAPH_COMPLETION,
    )

    formatted_results = []
    for r in results:
        if isinstance(r, str):
            formatted_results.append(r)
        else:
            try:
                formatted_results.append(json.dumps(r))
            except:
                formatted_results.append(str(r))
                
    return {"results": formatted_results, "query": query}


async def agent_chat(message: str, session_id: str = None, history: list = None) -> dict:
    """
    The core AI agent: recalls from Cognee graph memory, then reasons with an LLM.
    Fallback chain: Aerolink (LLM_API_KEY) → Gemini (GEMINI_API_KEY).
    Memory persists across sessions; the agent gets context, not amnesia.
    """
    # 1. Recall relevant memory from Cognee's knowledge graph
    memory = await recall_audit(message, session_id)
    memory_context = memory["results"]
    context_str = "\n".join(memory_context) if memory_context else "No relevant records found in memory."

    # 2. Build the user prompt with injected Cognee context
    grounded_user_message = (
        f"[Memory retrieved from Cognee knowledge graph]\n"
        f"{context_str}\n\n"
        f"[Question]\n{message}"
    )

    last_error = None

    # ── Path A: Aerolink via Anthropic SDK (LLM_API_KEY) ──────────────────────
    aerolink_key = os.getenv("LLM_API_KEY")
    if aerolink_key:
        try:
            response_text, model_used = await _call_anthropic(
                api_key=aerolink_key,
                system=AGENT_SYSTEM_PROMPT,
                history=history or [],
                user_message=grounded_user_message,
            )
            return _chat_result(response_text, model_used, memory_context, session_id)
        except Exception as e:
            last_error = e
            logger.warning(f"Aerolink/Anthropic call failed ({type(e).__name__}: {e}), falling back to Gemini")

    # ── Path B: Google Gemini fallback ────────────────────────────────────────
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            response_text, model_used = await _call_gemini(
                api_key=gemini_key,
                system=AGENT_SYSTEM_PROMPT,
                history=history or [],
                user_message=grounded_user_message,
            )
            return _chat_result(response_text, model_used, memory_context, session_id)
        except Exception as e:
            last_error = e
            logger.error(f"Gemini fallback also failed: {e}")

    raise ValueError(
        f"All LLM providers failed. Last error: {last_error}. "
        "Set LLM_API_KEY (Aerolink) and/or GEMINI_API_KEY in .env."
    )


async def _call_anthropic(api_key: str, system: str, history: list, user_message: str) -> tuple[str, str]:
    """Call the Anthropic-compatible API (used by Aerolink and direct Anthropic keys)."""
    import anthropic
    model = os.getenv("AGENT_LLM_MODEL", "claude-sonnet-4-6")
    base_url = os.getenv("ANTHROPIC_BASE_URL")
    messages = [{"role": h["role"], "content": h["content"]} for h in history]
    messages.append({"role": "user", "content": user_message})
    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    client = anthropic.AsyncAnthropic(**kwargs)
    resp = await client.messages.create(model=model, max_tokens=1024, system=system, messages=messages)
    return resp.content[0].text, model


async def _call_gemini(api_key: str, system: str, history: list, user_message: str) -> tuple[str, str]:
    """Call Google Gemini as the fallback LLM (uses google-genai, the current SDK)."""
    from google import genai
    from google.genai import types
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    client = genai.Client(api_key=api_key)

    # Build conversation history in Gemini format
    contents = []
    for h in history:
        role = "user" if h["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part(text=h["content"])]))
    contents.append(types.Content(role="user", parts=[types.Part(text=user_message)]))

    config = types.GenerateContentConfig(system_instruction=system, max_output_tokens=1024)
    resp = client.models.generate_content(model=model_name, contents=contents, config=config)
    return resp.text, model_name


def _chat_result(response_text: str, model: str, memory_context: list, session_id) -> dict:
    return {
        "response": response_text,
        "memory_context": memory_context,
        "memory_hits": len(memory_context),
        "model": model,
        "session_id": session_id,
    }


@retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
async def improve_session(session_id: str, datasets: list = None) -> dict:
    """
    Runs explicit enrichment pass on a session dataset.
    Called after all events for a session are ingested.
    """
    dataset_name = datasets[0] if datasets else f"session_{session_id}"
    await cognee.improve(
        dataset=dataset_name,
    )
    return {"status": "improved", "dataset": dataset_name}


async def forget_session(session_id: str, reason: str) -> dict:
    """
    NDPR/GDPR Article 17 surgical deletion.
    Removes session dataset from local stores and Cognee Cloud (if configured).
    """
    from . import cloud_sync as cs
    dataset_name = f"session_{session_id}"

    # Delete locally
    result = await cognee.forget(dataset=dataset_name)

    status = "failed"
    if result and isinstance(result, dict):
        status = result.get("status", "failed")

    if status != "deleted":
        raise Exception(f"Forget operation failed to verify deletion for {dataset_name}")

    # Clear local event caches
    _event_cache.pop(session_id, None)
    _event_data_cache.pop(session_id, None)

    # Best-effort cloud deletion — don't fail the whole operation if cloud is down
    cloud_status = "not_configured"
    try:
        cloud_result = await cs.forget_from_cloud(dataset_name)
        cloud_status = cloud_result.get("status", "unknown")
    except Exception as e:
        logger.warning(f"Cloud forget failed (non-fatal): {e}")
        cloud_status = "cloud_delete_failed"

    return {
        "status": status,
        "dataset": dataset_name,
        "reason": reason,
        "compliance": "NDPR Article 17 / GDPR Article 17",
        "timestamp": datetime.utcnow().isoformat(),
        "certificate_id": f"NDPR-{session_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "cloud_status": cloud_status,
    }


async def export_graph(session_id: str = None) -> str:
    """
    Exports Cognee's built-in graph visualization as HTML.
    Returns file path for frontend iframe.
    """
    from cognee.api.v1.visualize.visualize import visualize_graph
    import re
    safe_session_id = re.sub(r"[^a-zA-Z0-9_-]", "", session_id) if session_id else "all"
    path = f"../frontend/graph_{safe_session_id}.html" # Output to frontend dir so it can be served
    await visualize_graph(path)
    return path


_CONTROL_CHARS_RE = __import__('re').compile(r"[\x00-\x1f\x7f]")

def _safe(value, default="unknown") -> str:
    """Strip control characters from a string field before LLM interpolation."""
    if value is None:
        return default
    return _CONTROL_CHARS_RE.sub(" ", str(value)).strip()

def format_event_as_text(event: dict) -> str:
    """
    Formats structured event data as rich text for Cognee's graph extraction.
    Rich context = better entity + relationship extraction.
    All free-text fields are sanitized before interpolation to prevent prompt injection.
    """
    status = 'CLEAN'
    if event.get('confidence', 1.0) < 0.5:
        status = 'HIGH_RISK'
    elif event.get('confidence', 1.0) < 0.7:
        status = 'ANOMALY'

    return f"""
    IDENTITY_AUDIT_EVENT
    EventID: {_safe(event.get('event_id'), 'unknown')}
    User: {_safe(event.get('user_id'), 'unknown')} at {_safe(event.get('institution'), 'unknown')}
    Session: {_safe(event.get('session_id'), 'unknown')} (type: {_safe(event.get('session_type'), 'exam')})
    Event: {_safe(event.get('event_type'), 'unknown')}
    Confidence: {event.get('confidence')}
    Timestamp: {_safe(event.get('timestamp'), 'unknown')}
    Location: {_safe(event.get('location'), 'unknown')}
    Device: {_safe(event.get('device'), 'webcam')}
    Flag: {_safe(event.get('flag'), 'none')}
    Status: {status}
    Regulatory context: CBN Circular BSD/DIR/PUB/LAB/019/002, NDPR 2019
    """
