# XAIT Decision Engine API Documentation

The Decision Engine exposes several RESTful endpoints for evaluating decision payloads and dynamically managing the rules engine.

All endpoints require the API key to be passed in the headers:
```http
X-API-Key: <your_secret_api_key_here>
```

---

## 1. Decision Evaluation APIs

### `POST /v1/decisions/evaluate`
Evaluates an incoming payload against the active business rules and returns a decision.

- **Request Body (JSON):** The raw JSON payload (e.g., from a scraper or CRM). The internal mapper will normalize it based on `config/payload_mapping.yaml`.
- **Response:**
  ```json
  {
    "run_id": "uuid-string",
    "record_id": "record-123",
    "status": "completed",
    "approval_required": true,
    "final_decision": "additional_approval_required",
    "triggered_rules": [...],
    "rationale": "Margin is too low",
    "next_action": "send_email"
  }
  ```

### `POST /v1/decisions/restart/{run_id}`
Restarts a previously failed or halted decision pipeline run.

- **Request Body (JSON):**
  ```json
  {
    "restart_from_stage": "job_execution",
    "force": true,
    "reason": "Restarting after email server came back online"
  }
  ```

---

## 2. Rule Management APIs (Admin)

These endpoints power the Frontend UI, allowing administrators to dynamically adjust the rules engine without restarting the server. All changes take effect immediately for the next evaluation.

### `GET /v1/rules`
Fetches all currently configured rules from the database.

- **Response:**
  ```json
  [
    {
      "rule_id": "margin_check",
      "name": "Margin Check",
      "description": "Checks if margin is too low",
      "enabled": true,
      "priority": 100,
      "condition_group": "all",
      "conditions": [
        {"field": "margin", "operator": "less_than", "value": 0.20}
      ],
      "outcome": {
        "decision_effect": "require_additional_approval",
        "actions": [{"type": "send_email"}],
        "rationale_template": "Margin is below 20%"
      }
    }
  ]
  ```

### `POST /v1/rules`
Creates a brand new rule in the database.

- **Request Body (JSON):** The rule object (same structure as above).
- **Response:** The newly created rule.

### `PUT /v1/rules/{rule_id}`
Completely overwrites an existing rule with the provided payload. Use this when a user changes a threshold (e.g., changing margin from 20% to 30%).

- **Path Parameter:** `rule_id`
- **Request Body (JSON):** The updated rule object.
- **Response:** The updated rule.

### `DELETE /v1/rules/{rule_id}`
Deletes a rule from the database permanently.

- **Path Parameter:** `rule_id`
- **Response:** 
  ```json
  {
    "status": "success",
    "message": "Rule margin_check deleted."
  }
  ```
