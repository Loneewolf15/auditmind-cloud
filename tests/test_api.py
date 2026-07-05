import pytest
import os
from fastapi.testclient import TestClient
from backend.main import app
from unittest.mock import patch

client = TestClient(app, raise_server_exceptions=False)

# Minimal valid event payload reused across tests
VALID_EVENT = {
    "event_id": "test_1",
    "user_id": "user1",
    "session_id": "test_1",
    "event_type": "verification_pass",
    "confidence": 0.9,
    "timestamp": "2026-06-29T10:00:00Z"
}

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "auditmind-backend"}

def test_get_scenarios():
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    assert "clean_session" in response.json()

@patch('backend.cognee_service.remember_event')
def test_ingest_event(mock_remember):
    mock_remember.return_value = {"status": "success", "dataset": "session_test_1", "elapsed": 0.5}
    response = client.post("/api/event", json=VALID_EVENT)
    assert response.status_code == 200
    assert response.json()["status"] == "success"

@patch('backend.cognee_service.recall_audit')
def test_audit_query(mock_recall):
    mock_recall.return_value = {"results": ["test"], "query": "q"}
    response = client.post("/api/query", json={"query": "q", "session_id": "test"})
    assert response.status_code == 200
    assert "results" in response.json()

@patch('backend.cognee_service.improve_session')
def test_improve_session(mock_improve):
    mock_improve.return_value = {"status": "improved", "dataset": "test"}
    response = client.post("/api/improve/test_session")
    assert response.status_code == 200
    assert response.json()["status"] == "improved"

@patch('backend.cognee_service.forget_session')
def test_forget_data(mock_forget):
    mock_forget.return_value = {"status": "deleted"}
    response = client.request("DELETE", "/api/forget?session_id=test_session", json={"reason": "NDPR Article 17"})
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"

@patch('backend.cognee_service.export_graph')
def test_export_graph(mock_export):
    mock_export.return_value = "../frontend/graph_all.html"
    response = client.get("/api/graph/export")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_invalid_event_payload():
    response = client.post("/api/event", json={
        "event_id": "t1",
        "user_id": "u1",
        "session_id": "t1",
        "event_type": "verification_pass",
        "confidence": 1.5,  # invalid: > 1.0
        "timestamp": "2026"  # invalid: too short
    })
    assert response.status_code == 422
    assert response.json()["error_code"] == "VALIDATION_ERROR"

def test_invalid_event_type():
    payload = {**VALID_EVENT, "event_type": "invalid_type"}
    response = client.post("/api/event", json=payload)
    assert response.status_code == 422
    assert response.json()["error_code"] == "VALIDATION_ERROR"

def test_invalid_session_type():
    payload = {**VALID_EVENT, "session_type": "hack"}
    response = client.post("/api/event", json=payload)
    assert response.status_code == 422
    assert response.json()["error_code"] == "VALIDATION_ERROR"

def test_invalid_timestamp():
    payload = {**VALID_EVENT, "timestamp": "not-a-date-xxx"}
    response = client.post("/api/event", json=payload)
    assert response.status_code == 422
    assert response.json()["error_code"] == "VALIDATION_ERROR"

def test_cors_headers():
    # CORS must reflect the specific allowed origin, never wildcard "*"
    origin = "http://localhost:3000"
    response = client.options(
        "/api/event",
        headers={"Origin": origin, "Access-Control-Request-Method": "POST"}
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == origin
    assert response.headers["access-control-allow-origin"] != "*"

@patch('backend.cognee_service.recall_audit')
def test_global_exception_handler_does_not_leak_internals(mock_recall):
    mock_recall.side_effect = Exception("Simulated DB failure: connection string=db://secret")
    response = client.post("/api/query", json={"query": "test query", "session_id": "test_session"})
    assert response.status_code == 500
    assert response.json()["error_code"] == "SERVER_ERROR"
    # Internal error details must NOT be exposed to the client
    assert "Simulated DB failure" not in response.json()["message"]
    assert "secret" not in response.json()["message"]
    assert "internal error" in response.json()["message"].lower()

def test_forget_requires_api_key(monkeypatch):
    monkeypatch.setenv("AUDITMIND_API_KEY", "test-secret-key")
    import importlib, backend.main
    importlib.reload(backend.main)
    # Reload client against reloaded app
    from fastapi.testclient import TestClient
    fresh_client = TestClient(backend.main.app, raise_server_exceptions=False)
    response = fresh_client.request(
        "DELETE", "/api/forget?session_id=test_session",
        json={"reason": "NDPR Article 17 request"}
    )
    assert response.status_code == 401

@patch('backend.cognee_service.forget_session')
def test_forget_with_valid_api_key(mock_forget, monkeypatch):
    monkeypatch.setenv("AUDITMIND_API_KEY", "test-secret-key")
    import importlib, backend.main
    importlib.reload(backend.main)
    from fastapi.testclient import TestClient
    fresh_client = TestClient(backend.main.app, raise_server_exceptions=False)
    mock_forget.return_value = {"status": "deleted", "certificate_id": "NDPR-test-123"}
    response = fresh_client.request(
        "DELETE", "/api/forget?session_id=test_session",
        json={"reason": "NDPR Article 17 request"},
        headers={"X-API-Key": "test-secret-key"}
    )
    assert response.status_code == 200

@patch('backend.cognee_service.improve_session')
def test_improve_does_not_require_api_key(mock_improve, monkeypatch):
    # improve() enriches the graph — not destructive, so no API key required
    mock_improve.return_value = {"status": "improved", "dataset": "session_test_session"}
    monkeypatch.setenv("AUDITMIND_API_KEY", "test-secret-key")
    import importlib, backend.main
    importlib.reload(backend.main)
    from fastapi.testclient import TestClient
    fresh_client = TestClient(backend.main.app, raise_server_exceptions=False)
    response = fresh_client.post("/api/improve/test_session")
    assert response.status_code == 200

@patch('backend.cognee_service.agent_chat')
def test_chat_endpoint(mock_chat):
    mock_chat.return_value = {
        "response": "No anomalies found.",
        "memory_context": ["session_test_1: verification_pass confidence=0.97"],
        "memory_hits": 1,
        "model": "claude-sonnet-4-6",
        "session_id": "test_1",
    }
    response = client.post("/api/chat", json={
        "message": "Were there any anomalies in session test_1?",
        "session_id": "test_1",
        "history": []
    })
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "memory_context" in data
    assert data["memory_hits"] == 1

@patch('backend.cognee_service.agent_chat')
def test_chat_without_session_id(mock_chat):
    mock_chat.return_value = {
        "response": "I found fraud in session jamb_2026_fraud_002.",
        "memory_context": [],
        "memory_hits": 0,
        "model": "claude-sonnet-4-6",
        "session_id": None,
    }
    response = client.post("/api/chat", json={"message": "Any fraud detected?"})
    assert response.status_code == 200
    assert "response" in response.json()

def test_chat_empty_message():
    response = client.post("/api/chat", json={"message": ""})
    assert response.status_code == 422

def test_chat_message_too_long():
    response = client.post("/api/chat", json={"message": "x" * 2001})
    assert response.status_code == 422

@patch('backend.cognee_service.remember_event')
def test_graph_nodes_empty(mock_remember):
    response = client.get("/api/graph/nodes")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "links" in data
    assert "sessions" in data

def test_graph_nodes_after_ingest():
    import backend.cognee_service as cs
    cs._event_data_cache["test_1"] = [dict(VALID_EVENT)]
    try:
        response = client.get("/api/graph/nodes")
        assert response.status_code == 200
        data = response.json()
        assert any(n["id"] == "test_1" for n in data["nodes"])   # session node
        assert any(n["id"] == "user1" for n in data["nodes"])    # user node
        assert "test_1" in data["sessions"]
    finally:
        cs._event_data_cache.pop("test_1", None)

def test_mode_endpoint():
    response = client.get("/api/mode")
    assert response.status_code == 200
    data = response.json()
    assert "mode" in data
    assert data["mode"] in ("self-hosted", "cloud")
    assert "graph_db" in data
    assert "vector_db" in data
    assert "agent_model" in data

def test_mode_shows_self_hosted_for_kuzu(monkeypatch):
    monkeypatch.setenv("GRAPH_DATABASE_PROVIDER", "kuzu")
    monkeypatch.delenv("COGNEE_API_KEY", raising=False)
    import importlib, backend.main
    importlib.reload(backend.main)
    from fastapi.testclient import TestClient
    fresh_client = TestClient(backend.main.app, raise_server_exceptions=False)
    response = fresh_client.get("/api/mode")
    assert response.json()["mode"] == "self-hosted"
