import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.persistence.database import engine, Base
from app.persistence.seed import seed_rules
import uuid

Base.metadata.create_all(bind=engine)
seed_rules()

client = TestClient(app)
HEADERS = {"X-API-Key": "your_secret_api_key_here"}

def get_clean_payload(overrides=None):
    base = {
        "record_id": f"TEST-{uuid.uuid4()}",
        "source": "clean_source",
        "captured_at": "2026-07-07T12:00:00Z",
        "financials": {"total_price": 0.0, "margin": 0.5},
        "documents": {},
        "extracted_fields": {"status": "pending"},
        "workflow_context": {},
        "metadata": {"payload_version": "1.0"}
    }
    if overrides:
        # Simple top-level merge
        for k, v in overrides.items():
            if isinstance(v, dict) and k in base:
                base[k].update(v)
            else:
                base[k] = v
    return base

# --- Angle 1: Functional Happy Path ---

def test_clean_approval():
    payload = get_clean_payload({
        "extracted_fields": {"status": "approved"},
        "financials": {"total_price": 300000}
    })
    resp = client.post("/v1/decisions/evaluate", json=payload, headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["final_decision"] == "additional_approval_required"
    assert data["next_action"] == "send_email"
    assert len(data["executed_jobs"]) == 1

def test_clean_auto_approve():
    payload = get_clean_payload({
        "extracted_fields": {"status": "pending"},
        "financials": {"total_price": 10000}
    })
    resp = client.post("/v1/decisions/evaluate", json=payload, headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["final_decision"] == "no_additional_approval_required"

# --- Angle 2: Rule Engine Boundaries & Logic ---

def test_exact_boundary_value():
    payload = get_clean_payload({
        "financials": {"total_price": 250000}
    })
    resp = client.post("/v1/decisions/evaluate", json=payload, headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert any(r["rule_id"] == "high_total_price" for r in data["triggered_rules"])

def test_total_conflict():
    payload = get_clean_payload({
        "extracted_fields": {"status": "pending"},
        "financials": {"total_price": 300000}
    })
    resp = client.post("/v1/decisions/evaluate", json=payload, headers=HEADERS)
    data = resp.json()
    assert data["final_decision"] == "additional_approval_required"

def test_zero_rules_triggered():
    payload = get_clean_payload({
        "extracted_fields": {"status": "approved"},
        "financials": {"total_price": 1000}
    })
    resp = client.post("/v1/decisions/evaluate", json=payload, headers=HEADERS)
    assert resp.json()["final_decision"] == "no_additional_approval_required"

# --- Angle 3: Data Integrity & Mapping ---

def test_missing_record_id():
    resp = client.post("/v1/decisions/evaluate", json={"source": "test", "captured_at": "2026"}, headers=HEADERS)
    assert resp.status_code == 422

def test_type_casting_failure():
    # Sending a messy payload to trigger the mapper
    payload = {
        "meta": {"OpportunityID": f"TYPE-1-{uuid.uuid4()}", "SourceName": "messy_test", "Timestamp": "2026-07-07"},
        "financial_data": {"OrderValue": "FIVE HUNDRED"}
    }
    resp = client.post("/v1/decisions/evaluate", json=payload, headers=HEADERS)
    assert resp.status_code == 422

def test_massive_junk_payload():
    payload = get_clean_payload({
        "junk": ["a"] * 10000
    })
    resp = client.post("/v1/decisions/evaluate", json=payload, headers=HEADERS)
    assert resp.status_code == 200

# --- Angle 4: Idempotency & State ---

def test_duplicate_firing():
    payload = get_clean_payload({
        "financials": {"total_price": 300000}
    })
    resp1 = client.post("/v1/decisions/evaluate", json=payload, headers=HEADERS)
    run_id1 = resp1.json()["run_id"]
    
    resp2 = client.post("/v1/decisions/evaluate", json=payload, headers=HEADERS)
    run_id2 = resp2.json()["run_id"]
    
    assert run_id1 == run_id2

def test_invalid_restart_stage():
    # First create a valid run
    payload = get_clean_payload()
    resp = client.post("/v1/decisions/evaluate", json=payload, headers=HEADERS)
    run_id = resp.json()["run_id"]
    
    # Then attempt invalid restart
    resp = client.post(f"/v1/runs/{run_id}/restart", json={"restart_from_stage": "fake_stage"}, headers=HEADERS)
    assert resp.status_code == 400

def test_restart_completed_run():
    payload = get_clean_payload()
    resp = client.post("/v1/decisions/evaluate", json=payload, headers=HEADERS)
    run_id = resp.json()["run_id"]
    
    restart_resp = client.post(f"/v1/runs/{run_id}/restart", json={"restart_from_stage": "rule_evaluation"}, headers=HEADERS)
    assert restart_resp.status_code == 400
    
    restart_force = client.post(f"/v1/runs/{run_id}/restart", json={"restart_from_stage": "rule_evaluation", "force": True}, headers=HEADERS)
    assert restart_force.status_code == 200

# --- Angle 5: Security ---

def test_missing_api_key():
    resp = client.post("/v1/decisions/evaluate", json={})
    assert resp.status_code == 403

def test_sql_injection_attempt():
    payload = get_clean_payload({
        "record_id": "'; DROP TABLE runs; --"
    })
    resp = client.post("/v1/decisions/evaluate", json=payload, headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["record_id"] == "'; DROP TABLE runs; --"
