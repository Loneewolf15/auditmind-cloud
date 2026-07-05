"""
Cognee Cloud sync client.

AuditMind runs local-first (kuzu + lancedb) for speed and offline capability.
This module pushes the same events to your Cognee Cloud tenant on demand,
making them visible on the Cognee dashboard for the Cloud prize demo.

Flow per sync:
  1. POST /api/v1/add_text   — ingest formatted event text into cloud dataset
  2. POST /api/v1/cognify    — build the knowledge graph in the cloud
"""

import os
import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)

CLOUD_BASE_URL = os.getenv("COGNEE_CLOUD_BASE_URL", "").rstrip("/")
CLOUD_API_KEY  = os.getenv("COGNEE_CLOUD_API_KEY", "")
CLOUD_TENANT_ID = os.getenv("COGNEE_CLOUD_TENANT_ID", "")

TIMEOUT = httpx.Timeout(60.0, connect=10.0)


def _is_configured() -> bool:
    return bool(CLOUD_BASE_URL and CLOUD_API_KEY and CLOUD_TENANT_ID)


def _headers() -> dict:
    return {
        "X-Api-Key": CLOUD_API_KEY,
        "X-Tenant-Id": CLOUD_TENANT_ID,
        "Content-Type": "application/json",
    }


async def sync_session_to_cloud(dataset_name: str, event_texts: list[str]) -> dict:
    """
    Sync a list of pre-formatted event text strings to Cognee Cloud.
    Calls add_text to ingest, then cognify to build the graph.

    Returns a status dict with details for the frontend to display.
    """
    if not _is_configured():
        raise ValueError(
            "Cognee Cloud is not configured. "
            "Set COGNEE_CLOUD_BASE_URL, COGNEE_CLOUD_API_KEY, and COGNEE_CLOUD_TENANT_ID in .env"
        )

    if not event_texts:
        raise ValueError("No events to sync — run a scenario first to ingest events locally.")

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        # Step 1: Add text data to the cloud dataset
        # Cognee Cloud API: POST /api/v1/add accepts {"data": ..., "datasetName": ...}
        headers = _headers()
        headers.pop("Content-Type", None)  # let httpx set multipart/form-data boundary
        add_resp = await client.post(
            f"{CLOUD_BASE_URL}/api/v1/add",
            headers=headers,
            data={"datasetName": dataset_name},
            files={"data": ("events.txt", "\n\n".join(event_texts).encode("utf-8"))},
        )
        add_resp.raise_for_status()
        logger.info(f"Cloud add for {dataset_name}: {add_resp.status_code}")

        # Step 2: Cognify — build the knowledge graph from the ingested text
        cognify_resp = await client.post(
            f"{CLOUD_BASE_URL}/api/v1/cognify",
            headers=_headers(),
            json={
                "datasets": [dataset_name],
                "runInBackground": False,
            },
        )
        cognify_resp.raise_for_status()
        logger.info(f"Cloud cognify for {dataset_name}: {cognify_resp.status_code}")

    return {
        "status": "synced",
        "dataset": dataset_name,
        "events_synced": len(event_texts),
        "cloud_url": CLOUD_BASE_URL,
        "tenant_id": CLOUD_TENANT_ID,
    }


async def forget_from_cloud(dataset_name: str) -> dict:
    """
    Remove a dataset from Cognee Cloud (called alongside local forget for NDPR compliance).
    """
    if not _is_configured():
        logger.warning("Cognee Cloud not configured — skipping cloud forget")
        return {"status": "skipped", "reason": "cloud not configured"}

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(
            f"{CLOUD_BASE_URL}/api/v1/forget",
            headers=_headers(),
            json={"dataset": dataset_name},
        )
        resp.raise_for_status()

    return {"status": "deleted_from_cloud", "dataset": dataset_name}


def cloud_configured() -> bool:
    return _is_configured()
