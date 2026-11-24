# Phase 6 — Local Integration Gateway

## Run locally
```bash
pip install -r requirements.txt
export GATEWAY_API_KEY="replace-with-a-long-random-local-secret"
uvicorn gateway.app:app --reload --port 8000
```

By default, SQLite persists data at `gateway/data/gateway.db`. Override the location with `GATEWAY_DB_PATH` when needed. The database directory is created automatically.

Health: `GET http://127.0.0.1:8000/health`

Interactive API docs: `http://127.0.0.1:8000/docs`

## Authenticated endpoints
- `POST /v1/events` — validate the shared customer lifecycle event contract, deduplicate by eventId and persist a synthetic event.
- `GET /v1/events/{correlation_id}` — retrieve accepted events for a journey correlation ID.
- `POST /v1/crm-actions` — validate and persist a Salesforce action proposal, always in PENDING_HUMAN_APPROVAL.
- `GET /v1/audit?limit=100` — inspect the persisted audit trail.

Send `Authorization: Bearer <GATEWAY_API_KEY>` to all endpoints except health.

## Storage and safety
SQLite now provides local durability for events, CRM action proposals, and audit records across process restarts. Event IDs and action request IDs are unique keys, and correlation IDs are indexed for retrieval.

This remains a local proof-of-concept, not a production integration. It has no managed database, distributed queue, retry worker, dead-letter queue, rate limiting, tenant authentication, Adobe connector or Salesforce connector. CRM proposals are stored but never executed. Do not expose this service publicly or submit real customer data. A production design needs managed PostgreSQL, managed secrets, TLS, OAuth/service identities, least privilege, observability, schema versioning, privacy review, backup/restore procedures and threat modelling.

## Tests
```bash
pytest -q
```
