#!/bin/bash
# test_messy_evaluate.sh
# This script tests the engine with a messy JSON payload that mimics an Azure Foundry agent.
# The payload is automatically mapped using config/payload_mapping.yaml

echo "Sending Messy Payload (Azure Foundry Agent format) to XAIT Decision Engine..."

curl -s -X POST "http://localhost:8000/v1/decisions/evaluate" \
  -H "X-API-Key: your_secret_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {
        "SourceName": "messy_azure_agent",
        "OpportunityID": "MESSY-OPP-999",
        "Timestamp": "2026-07-07T12:00:00Z",
        "Version": "azure-v1"
    },
    "financial_data": {
        "OrderValue": "80000",
        "Cost": "70000",
        "MarginPercentage": "0.12"
    },
    "docs": {
        "HasSummary": "no",
        "HasSOW": "false"
    },
    "status": "Needs Approval"
}' | python3 -m json.tool
