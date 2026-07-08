#!/bin/bash
# test_edge_cases.sh
# A script simulating edge cases and failure scenarios to ensure the engine fails gracefully.

API_URL="http://localhost:8000/v1/decisions/evaluate"
API_KEY="your_secret_api_key_here"

echo "=========================================="
echo "1. Testing Empty Payload (Should return 422)"
echo "=========================================="
curl -s -X POST $API_URL \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}' | python3 -m json.tool

echo ""
echo "=========================================="
echo "2. Testing Unauthorized Access (Should return 403)"
echo "=========================================="
curl -s -X POST $API_URL \
  -H "X-API-Key: invalid-hacker-key" \
  -H "Content-Type: application/json" \
  -d '{"record_id": "test"}' | python3 -m json.tool

echo ""
echo "=========================================="
echo "3. Testing Type Mismatches in Messy Payload (Should return 422)"
echo "=========================================="
curl -s -X POST $API_URL \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {
        "SourceName": "messy_azure_agent",
        "OpportunityID": "MESSY-OPP-999"
    },
    "financial_data": {
        "OrderValue": "NOT_A_NUMBER"
    }
}' | python3 -m json.tool

echo ""
echo "=========================================="
echo "All resilience tests executed."
echo "=========================================="
