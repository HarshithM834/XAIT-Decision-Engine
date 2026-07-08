# XAIT Approval Decision Engine

A robust, production-ready backend service that acts as a post-extraction decision engine. It accepts a normalized JSON record payload, evaluates it against configurable YAML rules, and deterministicly outputs an approval decision and executes downstream actions (like sending an email).

## What it does
- Validates normalized JSON payloads representing business records.
- Evaluates them against externally configurable YAML business rules.
- Determines if additional approvals are required based on conditions.
- Executes downstream jobs (currently Email via Mock/SMTP).
- Tracks the lifecycle and status of the decision run.
- Exposes REST API endpoints to evaluate, view status, and restart runs from a specific stage.
- Persists all states to a local SQLite database (easily configurable for Postgres).

## What it does NOT do
- It does not extract or scrape data from upstream sources.
- It is not a frontend UI or a chat bot.
- It does not contain hardcoded business logic in the Python source code.

## Architecture Overview

The system is built with FastAPI, Pydantic, and SQLAlchemy, following Clean Architecture principles:
- **API endpoints** (`app/api/`) handle HTTP requests.
- **Services** (`app/services/`) manage the orchestration and run states.
- **Rules Engine** (`app/rules/`) evaluates the payloads against `config/rules.yaml`.
- **Jobs Framework** (`app/jobs/`) executes side effects based on rule outcomes.
- **Persistence** (`app/persistence/`) manages the SQLite database using Alembic for migrations.

## Lifecycle Stages
A run progresses through:
1. `received`
2. `validated`
3. `normalized`
4. `rule_evaluation`
5. `decision_generated`
6. `job_execution`
7. `completed` (or `failed`)

## Setup and Running Locally

1. Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   ```
2. Build and run via Docker Compose:
   ```bash
   make docker-up
   ```
   Or via standard docker-compose:
   ```bash
   docker-compose up --build
   ```

The API will be available at `http://localhost:8000`.

## API Authentication

All endpoints under `/v1/` (except health checks) require the `X-API-Key` header.
- **Header:** `X-API-Key`
- **Value:** Configured in your `.env` via `API_KEY`

## Sample Requests

### Evaluate a Decision
```bash
curl -X POST http://localhost:8000/v1/decisions/evaluate \
  -H "X-API-Key: your_secret_api_key_here" \
  -H "Content-Type: application/json" \
  -d @sample_payload.json
```

### Get Run Status
```bash
curl -X GET http://localhost:8000/v1/runs/<run_id_here> \
  -H "X-API-Key: your_secret_api_key_here"
```

### Restart a Run
```bash
curl -X POST http://localhost:8000/v1/runs/<run_id_here>/restart \
  -H "X-API-Key: your_secret_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{"restart_from_stage": "rule_evaluation", "reason": "Data updated manually"}'
```

## Configurable Rules
Rules are defined in `config/rules.yaml`. You can modify these without changing code.
The engine evaluates all rules, collects outcomes, and resolves conflicts deterministically.

## Idempotency
Submitting the exact same payload multiple times will not create new runs or trigger duplicate side effects (unless the `force=true` query parameter is used). The engine will return the result of the previously completed run.
