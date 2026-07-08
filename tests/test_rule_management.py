import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.persistence.database import engine, Base
from app.persistence.seed import seed_rules

Base.metadata.create_all(bind=engine)
seed_rules()

client = TestClient(app)
HEADERS = {"X-API-Key": "your_secret_api_key_here"}

def test_get_rules():
    resp = client.get("/v1/rules", headers=HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()) > 0 # Initial rules are seeded

def test_create_read_update_delete_rule():
    new_rule = {
        "rule_id": "test_crud_rule",
        "name": "Test CRUD",
        "description": "Just testing",
        "enabled": True,
        "priority": 100,
        "condition_group": "all",
        "conditions": [{"field": "test_field", "operator": "exists", "value": None}],
        "outcome": {
            "decision_effect": "flag_for_review",
            "actions": [{"type": "none"}],
            "rationale_template": "Test"
        }
    }
    
    # 1. Create
    resp = client.post("/v1/rules", json=new_rule, headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["rule_id"] == "test_crud_rule"
    
    # 2. Get
    resp = client.get("/v1/rules", headers=HEADERS)
    rules = resp.json()
    assert any(r["rule_id"] == "test_crud_rule" for r in rules)
    
    # 3. Update
    new_rule["name"] = "Updated Name"
    new_rule["priority"] = 999
    resp = client.put("/v1/rules/test_crud_rule", json=new_rule, headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Name"
    assert resp.json()["priority"] == 999.0
    
    # 4. Delete
    resp = client.delete("/v1/rules/test_crud_rule", headers=HEADERS)
    assert resp.status_code == 200
    
    # Verify deletion
    resp = client.get("/v1/rules", headers=HEADERS)
    rules = resp.json()
    assert not any(r["rule_id"] == "test_crud_rule" for r in rules)
