# Phase 6 — Local Integration Gateway

## Zero-cost local setup

The gateway runs locally with SQLite. No Render service, hosted database, Vercel project or paid account is required.

From the repository root:

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate

pip install -r gateway/requirements.txt
```

Set a local API key before starting the gateway.

Windows PowerShell:
```powershell
$env:GATEWAY_API_KEY = "replace-with-a-long-random-local-secret"
uvicorn gateway.app:app --reload --host 127.0.0.1 --port 8000
```

macOS/Linux:
```bash
export GATEWAY_API_KEY="replace-with-a-long-random-local-secret"
uvicorn gateway.app:app --reload --host 127.0.0.1 --port 8000
```

SQLite is the default and persists data at `gateway/data/gateway.db`. Override the file location with `GATEWAY_DB_PATH`. The database directory is created automatically.

- Health: http://127.0.0.1:8000/health
- Interactive API docs: http://127.0.0.1:8000/docs

The health endpoint should return `status: ok` and `storage: sqlite`.

## Authenticated endpoints

- `POST /v1/events` — validate the shared customer lifecycle event contract, deduplicate by eventId and persist a synthetic event.
- `GET /v1/events/{correlation_id}` — retrieve accepted events for a journey correlation ID.
- `POST /v1/crm-actions` — validate and persist a Salesforce action proposal, always in PENDING_HUMAN_APPROVAL.
- `GET /v1/audit?limit=100` — inspect the persisted audit trail.
- `POST /v1/retries` — enqueue a synthetic downstream task.
- `GET /v1/retries?status=PENDING|RETRY_SCHEDULED|DEAD_LETTER` — inspect retry and dead-letter jobs.
- `POST /v1/retries/{job_id}/fail` — record a failed attempt and schedule bounded exponential backoff; after the configured maximum, move the job to `DEAD_LETTER`.

Send `Authorization: Bearer <GATEWAY_API_KEY>` to all endpoints except health.

## Safety and limitations

This is a local synthetic proof-of-concept, not a production integration. CRM proposals are never executed. Retry jobs and dead-letter transitions are persisted, with a bounded attempt count (1–10) and exponential delay (60 seconds, doubling to a one-hour cap). It does not run a background worker or execute downstream delivery. It has no rate limiting, tenant authentication, Adobe connector or Salesforce connector. Do not submit real customer data.

SQLite is suitable for local single-user learning. PostgreSQL can be configured for a separate environment if needed, but hosted infrastructure is deliberately outside this zero-cost setup.

## Tests

From the repository root:

```bash
pytest -q tests/test_gateway.py tests/test_gateway_postgres.py
```

The PostgreSQL integration tests require a PostgreSQL test database; GitHub Actions provisions one for CI. Local gateway operation does not require PostgreSQL.
