# Phase 6 — Local Integration Gateway

## Run locally with SQLite
```bash
pip install -r requirements.txt
export GATEWAY_API_KEY="replace-with-a-long-random-local-secret"
uvicorn gateway.app:app --reload --port 8000
```

SQLite is the default and persists data at `gateway/data/gateway.db`. Override the file location with `GATEWAY_DB_PATH`. The database directory is created automatically.

## Configure PostgreSQL
Set `GATEWAY_DATABASE_URL` to a PostgreSQL connection string. The gateway accepts standard `postgresql://` and `postgres://` URLs and uses the Psycopg 3 driver.

```bash
export GATEWAY_DATABASE_URL="postgresql://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require"
export GATEWAY_API_KEY="replace-with-a-long-random-local-secret"
uvicorn gateway.app:app --host 0.0.0.0 --port 8000
```

Keep database credentials in the hosting platform's secret manager; never commit them to Git. Use a least-privilege database role and TLS. The application initializes the required tables and indexes on startup. For production, use managed schema migrations rather than relying on application startup DDL.

Health: `GET /health` — returns the active storage type after checking database connectivity.

Interactive API docs: `/docs`

## Authenticated endpoints
- `POST /v1/events` — validate the shared customer lifecycle event contract, deduplicate by eventId and persist a synthetic event.
- `GET /v1/events/{correlation_id}` — retrieve accepted events for a journey correlation ID.
- `POST /v1/crm-actions` — validate and persist a Salesforce action proposal, always in PENDING_HUMAN_APPROVAL.
- `GET /v1/audit?limit=100` — inspect the persisted audit trail.
- `POST /v1/retries` — enqueue a synthetic downstream task.
- `GET /v1/retries?status=PENDING|RETRY_SCHEDULED|DEAD_LETTER` — inspect retry and dead-letter jobs.
- `POST /v1/retries/{job_id}/fail` — record a failed attempt and schedule bounded exponential backoff; after the configured maximum, move the job to `DEAD_LETTER`.

Send `Authorization: Bearer <GATEWAY_API_KEY>` to all endpoints except health.

## Storage and safety
SQLite supports local learning and single-instance demonstrations. PostgreSQL is configurable for hosted environments and multi-client persistence. Events, CRM action proposals and audit records are stored in the selected database. CRM proposals are never executed.

This remains a synthetic proof-of-concept, not a production integration. Retry jobs and dead-letter transitions are persisted, with a bounded attempt count (1–10) and exponential delay (60 seconds, doubling to a one-hour cap). This phase provides queue-state primitives and a failure-recording endpoint for controlled demonstrations; it does not run a background worker or execute downstream delivery. It has no rate limiting, tenant authentication, Adobe connector or Salesforce connector. Do not submit real customer data. Production readiness still requires managed secrets, TLS, OAuth/service identities, least privilege, migrations, observability, backup/restore, privacy review, threat modelling and operational runbooks.

## Tests
```bash
pytest -q
```
