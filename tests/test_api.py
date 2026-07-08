import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.persistence.database import Base, engine

# Set up test database
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def test_health_check():
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}

def test_ready_check():
    response = client.get("/v1/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"

def test_missing_api_key():
    response = client.get("/v1/rules")
    assert response.status_code == 403

def test_evaluate_payload():
    payload = {
      "record_id": "TEST-001",
      "source": "SO Summary",
      "captured_at": "2026-07-07T12:00:00Z",
      "financials": {
        "total_price": 500000.0,
        "total_cost": 200000.0,
        "margin": 0.20
      },
      "documents": {
        "so_summary_found": True,
        "sow_found": False,
        "latest_document_timestamp": "2026-07-07T10:00:00Z",
        "source_mismatch_detected": False
      },
      "extracted_fields": {
        "status": "pending_review",
        "approval_threshold": "Tier 2",
        "approval_type": "Standard",
        "customer_name": "Test Corp",
        "region": "NA",
        "business_unit": "Enterprise"
      },
      "workflow_context": {
        "requested_start_stage": None,
        "restart_allowed": True,
        "initiated_by": "automation_bot"
      },
      "metadata": {
        "upstream_system": "Extractor",
        "payload_version": "1.0",
        "notes": "Test"
      }
    }
    
    headers = {"X-API-Key": "your_secret_api_key_here"}
    response = client.post("/v1/decisions/evaluate", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["record_id"] == "TEST-001"
    assert data["final_decision"] == "additional_approval_required"
    assert len(data["triggered_rules"]) > 0

def test_evaluate_missing_financials():
    payload = {
      "record_id": "TEST-002",
      "source": "SO Summary",
      "captured_at": "2026-07-07T12:00:00Z",
      "financials": {}, # Missing total_price and margin
      "documents": {},
      "extracted_fields": {},
      "workflow_context": {"restart_allowed": False},
      "metadata": {"payload_version": "1.0"}
    }
    headers = {"X-API-Key": "your_secret_api_key_here"}
    response = client.post("/v1/decisions/evaluate", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["final_decision"] == "validation_failed"

