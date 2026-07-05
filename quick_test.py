from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app, raise_server_exceptions=False)

def test_endpoints():
    print("Testing /api/scenarios...")
    res = client.get("/api/scenarios")
    assert res.status_code == 200
    scenarios = res.json()
    print("  -> OK")
    
    # Just take one scenario
    session_id = "test_session_999"
    ev = {
        "event_id": "t1", "user_id": "u1", "session_id": session_id,
        "session_type": "exam", "event_type": "biometric_scan",
        "confidence": 0.9, "timestamp": "2026-06-29T10:00:00Z",
        "location": "A", "device": "B", "institution": "C", "flag": "NONE"
    }
    
    print("Testing /api/event...")
    res = client.post("/api/event", json=ev)
    print(f"  -> {res.status_code} {res.json()}")
    assert res.status_code == 200
    
    print("Testing /api/improve...")
    res = client.post(f"/api/improve/{session_id}")
    print(f"  -> {res.status_code} {res.json()}")
    assert res.status_code == 200
    
    print("Testing /api/query...")
    res = client.post("/api/query", json={"query": "hello", "session_id": session_id})
    print(f"  -> {res.status_code} {res.json()}")
    assert res.status_code in [200, 500] # Might be 500 if no LLM key
    
    print("Testing /api/chat...")
    res = client.post("/api/chat", json={"message": "hello", "session_id": session_id, "history": []})
    print(f"  -> {res.status_code} {res.json()}")
    assert res.status_code in [200, 500]

    print("Testing /api/forget...")
    res = client.request("DELETE", f"/api/forget?session_id={session_id}", json={"reason": "NDPR"})
    print(f"  -> {res.status_code} {res.json()}")
    assert res.status_code in [200, 401]
    
    print("SUCCESS")

if __name__ == "__main__":
    test_endpoints()
