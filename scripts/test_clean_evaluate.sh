#!/bin/bash
# test_clean_evaluate.sh
# This script tests the engine with a perfectly clean NormalizedPayload.

echo "Sending Clean Payload to XAIT Decision Engine..."

curl -s -X POST "http://localhost:8000/v1/decisions/evaluate" \
  -H "X-API-Key: your_secret_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "record_id": "CLEAN-OPP-001",
    "source": "salesforce",
    "captured_at": "2026-07-07T12:00:00Z",
    "financials": {
        "total_price": 300000.0,
        "total_cost": 200000.0,
        "margin": 0.33
    },
    "documents": {
        "so_summary_found": true,
        "sow_found": true
    },
    "extracted_fields": {
        "status": "pending",
        "customer_name": "Acme Corp"
    },
    "workflow_context": {},
    "metadata": {
        "payload_version": "1.0"
    }
}' | python3 -m json.tool
