# Phase 6 — Local Integration Gateway

## Run locally
```bash
pip install -r requirements.txt
export GATEWAY_API_KEY="replace-with-a-long-random-local-secret"
uvicorn gateway.app:app --reload --port 8000
```

Health: `GET http://127.0.0.1:8000/health`

Interactive API docs: `http://127.0.0.1:8000/docs`

## Authenticated endpoints
- `POST /v1/events` — validate the shared customer lifecycle event contract, deduplicate by eventId and accept a synthetic event.
- `GET /v1/events/{correlation_id}` — retrieve accepted events for a journey correlation ID.
- `POST /v1/crm-actions` — validate a Salesforce action proposal and keep it in PENDING_HUMAN_APPROVAL.
- `GET /v1/audit?limit=100` — inspect the in-memory audit trail.

Send `Authorization: Bearer <GATEWAY_API_KEY>` to all endpoints except health.

## Important limits
This is a local proof-of-concept. Events, action proposals and audit records are held in process memory and disappear on restart. There is no durable queue, database, retry worker, dead-letter queue, distributed idempotency store, rate limiting, tenant authentication, Adobe connector or Salesforce connector. Do not expose this service publicly or submit real customer data. A production design needs durable storage, managed secrets, TLS, OAuth/service identities, least privilege, observability, schema versioning, privacy review and threat modelling.

## Tests
```bash
pytest -q
```
