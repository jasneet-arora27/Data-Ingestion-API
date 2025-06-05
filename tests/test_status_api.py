import sys
import os
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from fastapi.testclient import TestClient
from app.main import app
import time

client = TestClient(app)

# Add the wait_for_completion helper function
def wait_for_completion(ingestion_id, timeout=60):
    """Wait for ingestion to complete, with timeout."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        response = client.get(f"/status/{ingestion_id}")
        data = response.json()
        if data["status"] == "completed":
            return True
        time.sleep(1)
    return False

def test_status_api_triggered():
    # Simulate ingestion request
    response = client.post("/ingest", json={"ids": [1, 2, 3, 4, 5], "priority": "MEDIUM"})
    ingestion_id = response.json()["ingestion_id"]

    # Check status of the ingestion request
    response = client.get(f"/status/{ingestion_id}")
    assert response.status_code == 200
    assert response.json()["ingestion_id"] == ingestion_id
    assert response.json()["status"] == "triggered"

def test_status_api_completed():
    # Simulate ingestion request
    response = client.post("/ingest", json={"ids": [1, 2, 3], "priority": "HIGH"})
    ingestion_id = response.json()["ingestion_id"]

    # Wait for completion with helper function instead of fixed sleep
    assert wait_for_completion(ingestion_id), "Ingestion did not complete in time"

    # Check status of the ingestion request
    response = client.get(f"/status/{ingestion_id}")
    assert response.status_code == 200
    assert response.json()["ingestion_id"] == ingestion_id
    assert response.json()["status"] == "completed"
    assert all(batch["status"] == "completed" for batch in response.json()["batches"])

def test_status_api_yet_to_start():
    # Check status of a non-existent ingestion_id
    response = client.get("/status/non_existent_id")
    assert response.status_code == 404  # Assuming the API returns 404 for non-existent IDs

def test_status_api_priority_handling():
    # Simulate multiple ingestion requests
    response1 = client.post("/ingest", json={"ids": [1, 2, 3], "priority": "LOW"})
    ingestion_id1 = response1.json()["ingestion_id"]

    response2 = client.post("/ingest", json={"ids": [4, 5, 6], "priority": "HIGH"})
    ingestion_id2 = response2.json()["ingestion_id"]

    # Wait for completion using the helper function
    assert wait_for_completion(ingestion_id2), "High priority ingestion did not complete in time"
    assert wait_for_completion(ingestion_id1), "Low priority ingestion did not complete in time"

    # Check status of the high priority ingestion request
    response = client.get(f"/status/{ingestion_id2}")
    assert response.status_code == 200
    assert response.json()["status"] == "completed"

    # Check status of the low priority ingestion request
    response = client.get(f"/status/{ingestion_id1}")
    assert response.status_code == 200
    assert response.json()["status"] == "completed"