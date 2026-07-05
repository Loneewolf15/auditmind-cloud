import asyncio
from dotenv import load_dotenv
load_dotenv(".env.cloud")
import uuid
from backend.cloud_sync import sync_session_to_cloud, forget_from_cloud, _headers, CLOUD_BASE_URL
import httpx

async def main():
    print("Testing cloud sync with unique dataset name...")
    dataset_name = f"test_dataset_{uuid.uuid4().hex[:8]}"
    events = [
        "IDENTITY_AUDIT_EVENT\nEventID: test_001\nUser: test_user\nSession: test_session\nEvent: verification_pass\nConfidence: 0.95"
    ]
    try:
        res = await sync_session_to_cloud(dataset_name, events)
        print("Sync result:", res)
        print("Testing forget from cloud...")
        res_forget = await forget_from_cloud(dataset_name)
        print("Forget result:", res_forget)
        print("SUCCESS! Cloud integration is working.")
    except httpx.HTTPStatusError as e:
        print("HTTP ERROR:", e)
        print("Response Text:", e.response.text)
    except Exception as e:
        print("FAILED:", e)

asyncio.run(main())
