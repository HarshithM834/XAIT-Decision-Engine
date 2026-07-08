from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)

# Bypass API Key by providing a valid mock (DEV_MODE is false in tests usually)
HEADERS = {"X-API-Key": "your_secret_api_key_here"}

def test_empty_payload():
    """Test sending an entirely empty payload."""
    response = client.post("/v1/decisions/evaluate", json={}, headers=HEADERS)
    # The API should gracefully return a 422 for missing record_id, not a 500
    assert response.status_code == 422

def test_missing_mapped_required_field():
    """Test sending a payload that the mapper processes, but is missing required root fields."""
    messy_payload = {
        "val": "150000.50",
        "has_doc": "yes"
    }
    # It will map val -> financials.total_price and has_doc -> documents.so_summary_found
    # But it won't map record_id, which is required.
    response = client.post("/v1/decisions/evaluate", json=messy_payload, headers=HEADERS)
    assert response.status_code == 422

def test_type_mismatch_casting():
    """Test the mapper gracefully ignoring or handling impossible type casts."""
    messy_payload = {
        "meta": {
            "OpportunityID": f"TEST-{uuid.uuid4()}",
            "SourceName": "messy_azure_agent"
        },
        "financial_data": {
            "OrderValue": "NOT_A_NUMBER", # Mapped to float
            "Cost": "ALSO_NOT_A_NUMBER"
        },
        "status": "pending"
    }
    response = client.post("/v1/decisions/evaluate", json=messy_payload, headers=HEADERS)
    
    # Validation should fail because the mapper couldn't cast NOT_A_NUMBER to float,
    # so it remained a string, and Pydantic will reject string in a float field (if strict)
    # or the mapper failed and skipped it. If Pydantic fails, it's a 422.
    assert response.status_code == 422

def test_idempotency_concurrency_simulation():
    """Test idempotency logic for duplicate requests."""
    payload = {
        "record_id": f"IDEMP-{uuid.uuid4()}",
        "source": "salesforce",
        "captured_at": "2026-07-07T12:00:00Z",
        "financials": {},
        "documents": {},
        "extracted_fields": {},
        "workflow_context": {},
        "metadata": {"payload_version": "1.0"}
    }
    
    # 1. First run should succeed (200 OK)
    resp1 = client.post("/v1/decisions/evaluate", json=payload, headers=HEADERS)
    assert resp1.status_code == 200
    data1 = resp1.json()
    run_id = data1["run_id"]
    
    # 2. Duplicate run should return 200 OK with the exact SAME run_id
    resp2 = client.post("/v1/decisions/evaluate", json=payload, headers=HEADERS)
    assert resp2.status_code == 200
    data2 = resp2.json()
    
    assert data1["run_id"] == data2["run_id"]
    assert data2["current_stage"] == "completed"

def test_restart_completed_run():
    """Test restarting a run that is already complete."""
    payload = {
        "record_id": f"RESTART-{uuid.uuid4()}",
        "source": "salesforce",
        "captured_at": "2026-07-07T12:00:00Z",
        "financials": {},
        "documents": {},
        "extracted_fields": {},
        "workflow_context": {},
        "metadata": {"payload_version": "1.0"}
    }
    
    # Create the run
    resp = client.post("/v1/decisions/evaluate", json=payload, headers=HEADERS)
    run_id = resp.json()["run_id"]
    
    # Attempt to restart a completed run
    restart_resp = client.post(f"/v1/runs/{run_id}/restart", json={"restart_from_stage": "rule_evaluation"}, headers=HEADERS)
    # The API throws a 400 Bad Request if you restart a run that's already completed or not allowed
    assert restart_resp.status_code == 400

def test_invalid_api_key():
    """Test unauthorized access."""
    response = client.post("/v1/decisions/evaluate", json={}, headers={"X-API-Key": "hacker123"})
    assert response.status_code == 403
