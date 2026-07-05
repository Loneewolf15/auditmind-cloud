import requests
import json
import time

API_BASE = "http://localhost:8000"

def verify_scenarios():
    print("Fetching scenarios...")
    res = requests.get(f"{API_BASE}/api/scenarios")
    scenarios = res.json()
    print(f"Loaded {len(scenarios)} scenarios.")
    
    for key, events in scenarios.items():
        print(f"\n--- Verifying Scenario: {key} ---")
        session_id = events[0]['session_id']
        
        # 1. Ingest events
        print("1. Ingesting events...")
        for ev in events:
            ev['session_id'] = session_id
            resp = requests.post(f"{API_BASE}/api/event", json=ev)
            print(f"  Ingest {ev['event_id']} -> {resp.status_code}")
        
        # 2. Improve session
        print("2. Improving session...")
        resp = requests.post(f"{API_BASE}/api/improve/{session_id}")
        print(f"  Improve -> {resp.status_code}")
        
        # 3. Query audit
        print("3. Querying audit trail...")
        query_payload = {
            "query": "Show all events",
            "session_id": session_id
        }
        resp = requests.post(f"{API_BASE}/api/query", json=query_payload)
        print(f"  Query -> {resp.status_code}")
        
        # 4. If NDPR Purge, run forget
        if key == "ndpr_purge":
            print("4. Executing NDPR Purge...")
            forget_payload = {"reason": "User requested data deletion per NDPR Art 17"}
            # using requests to send DELETE with body
            resp = requests.request("DELETE", f"{API_BASE}/api/forget?session_id={session_id}", json=forget_payload)
            print(f"  Forget -> {resp.status_code}")

if __name__ == "__main__":
    verify_scenarios()
