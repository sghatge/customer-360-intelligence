"""Contract-first synthetic MarTech gateway with SQLite/PostgreSQL persistence."""
from __future__ import annotations

import hmac
import json
import os
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from fastapi import Depends, FastAPI, Header, HTTPException
from jsonschema import Draft202012Validator, FormatChecker
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection

ROOT = Path(__file__).resolve().parents[1]
EVENT_SCHEMA = json.loads((ROOT / "contracts/customer-lifecycle-event.json").read_text())
ACTION_SCHEMA = json.loads((ROOT / "contracts/salesforce-followup-action.json").read_text())
event_validator = Draft202012Validator(EVENT_SCHEMA, format_checker=FormatChecker())
action_validator = Draft202012Validator(ACTION_SCHEMA, format_checker=FormatChecker())

app = FastAPI(title="MarTech Lifecycle Integration Gateway", version="0.3.0",
              description="Synthetic contract-validation gateway with configurable SQL persistence.")

def database_url() -> str:
    configured = os.getenv("GATEWAY_DATABASE_URL")
    if configured:
        return configured
    path = Path(os.getenv("GATEWAY_DB_PATH", str(ROOT / "gateway" / "data" / "gateway.db")))
    path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{path}"

@contextmanager
def connect() -> Iterator[Connection]:
    engine = create_engine(database_url(), pool_pre_ping=True)
    try:
        with engine.begin() as connection:
            yield connection
    finally:
        engine.dispose()

def init_db() -> None:
    statements = [
        """CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY, correlation_id TEXT NOT NULL,
            payload TEXT NOT NULL, created_at TEXT NOT NULL)""",
        "CREATE INDEX IF NOT EXISTS idx_events_correlation ON events(correlation_id)",
        """CREATE TABLE IF NOT EXISTS crm_actions (
            request_id TEXT PRIMARY KEY, correlation_id TEXT NOT NULL,
            payload TEXT NOT NULL, created_at TEXT NOT NULL)""",
        "CREATE INDEX IF NOT EXISTS idx_actions_correlation ON crm_actions(correlation_id)",
        """CREATE TABLE IF NOT EXISTS audit (
            audit_id TEXT PRIMARY KEY, occurred_at TEXT NOT NULL,
            action TEXT NOT NULL, correlation_id TEXT NOT NULL,
            status TEXT NOT NULL, detail TEXT NOT NULL)""",
    ]
    with connect() as conn:
        for statement in statements:
            conn.execute(text(statement))

init_db()

def require_api_key(authorization: str | None = Header(default=None)) -> None:
    expected = os.getenv("GATEWAY_API_KEY", "")
    if not expected:
        raise HTTPException(status_code=503, detail="Gateway API key is not configured")
    supplied = authorization.removeprefix("Bearer ").strip() if authorization else ""
    if not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Invalid bearer token")

def schema_errors(validator: Draft202012Validator, payload: dict[str, Any]) -> list[str]:
    return [f"{'.'.join(map(str, err.absolute_path)) or '$'}: {err.message}"
            for err in sorted(validator.iter_errors(payload), key=lambda e: list(map(str, e.absolute_path)))]

def audit(action: str, correlation_id: str, status: str, detail: str) -> None:
    with connect() as conn:
        conn.execute(text("""INSERT INTO audit
            (audit_id, occurred_at, action, correlation_id, status, detail)
            VALUES (:id, :at, :action, :correlation, :status, :detail)"""),
            {"id": str(uuid.uuid4()), "at": datetime.now(timezone.utc).isoformat(),
             "action": action, "correlation": correlation_id, "status": status, "detail": detail})

@app.get("/health")
def health() -> dict[str, str]:
    try:
        with connect() as conn:
            conn.execute(text("SELECT 1"))
        backend = "postgresql" if database_url().startswith(("postgresql://", "postgres://", "postgresql+")) else "sqlite"
        return {"status": "ok", "storage": backend, "mode": "synthetic"}
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable")

@app.post("/v1/events", dependencies=[Depends(require_api_key)])
def ingest_event(payload: dict[str, Any]) -> dict[str, Any]:
    errors = schema_errors(event_validator, payload)
    if errors:
        audit("EVENT_VALIDATION", str(payload.get("correlationId", "UNKNOWN")), "REJECTED", "; ".join(errors))
        raise HTTPException(status_code=422, detail={"contract": "customer-lifecycle-event", "errors": errors})
    event_id, correlation_id = payload["eventId"], payload["correlationId"]
    with connect() as conn:
        existing = conn.execute(text("SELECT 1 FROM events WHERE event_id=:id"), {"id": event_id}).first()
        if existing:
            duplicate = True
        else:
            conn.execute(text("""INSERT INTO events (event_id, correlation_id, payload, created_at)
                VALUES (:id, :correlation, :payload, :created)"""),
                {"id": event_id, "correlation": correlation_id, "payload": json.dumps(payload),
                 "created": datetime.now(timezone.utc).isoformat()})
            duplicate = False
    if duplicate:
        audit("EVENT_INGEST", correlation_id, "DUPLICATE", event_id)
        return {"status": "DUPLICATE_IGNORED", "eventId": event_id, "correlationId": correlation_id}
    audit("EVENT_INGEST", correlation_id, "ACCEPTED", event_id)
    return {"status": "ACCEPTED", "eventId": event_id, "correlationId": correlation_id}

@app.get("/v1/events/{correlation_id}", dependencies=[Depends(require_api_key)])
def get_events(correlation_id: str) -> dict[str, Any]:
    with connect() as conn:
        rows = conn.execute(text("""SELECT payload FROM events WHERE correlation_id=:id
            ORDER BY created_at"""), {"id": correlation_id}).mappings().all()
    events = [json.loads(row["payload"]) for row in rows]
    return {"correlationId": correlation_id, "count": len(events), "events": events}

@app.post("/v1/crm-actions", dependencies=[Depends(require_api_key)])
def propose_crm_action(payload: dict[str, Any]) -> dict[str, Any]:
    errors = schema_errors(action_validator, payload)
    if errors:
        audit("CRM_ACTION_VALIDATION", str(payload.get("correlationId", "UNKNOWN")), "REJECTED", "; ".join(errors))
        raise HTTPException(status_code=422, detail={"contract": "salesforce-followup-action", "errors": errors})
    correlation_id = payload["correlationId"]
    if payload["requiresHumanApproval"] is not True or payload["status"] != "PENDING_HUMAN_APPROVAL":
        audit("CRM_ACTION_POLICY", correlation_id, "REJECTED", "Human approval is mandatory")
        raise HTTPException(status_code=403, detail="CRM action must remain pending human approval")
    request_id = payload["requestId"]
    with connect() as conn:
        existing = conn.execute(text("SELECT 1 FROM crm_actions WHERE request_id=:id"),
                                {"id": request_id}).first()
        if not existing:
            conn.execute(text("""INSERT INTO crm_actions
                (request_id, correlation_id, payload, created_at)
                VALUES (:id, :correlation, :payload, :created)"""),
                {"id": request_id, "correlation": correlation_id, "payload": json.dumps(payload),
                 "created": datetime.now(timezone.utc).isoformat()})
    if existing:
        audit("CRM_ACTION", correlation_id, "DUPLICATE", request_id)
        return {"status": "DUPLICATE_IGNORED", "requestId": request_id}
    audit("CRM_ACTION", correlation_id, "PENDING_HUMAN_APPROVAL", request_id)
    return {"status": "PENDING_HUMAN_APPROVAL", "requestId": request_id,
            "correlationId": correlation_id, "executed": False}

@app.get("/v1/audit", dependencies=[Depends(require_api_key)])
def get_audit(limit: int = 100) -> dict[str, Any]:
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 500")
    with connect() as conn:
        rows = conn.execute(text("""SELECT * FROM audit ORDER BY occurred_at DESC
            LIMIT :limit"""), {"limit": limit}).mappings().all()
    records = [dict(row) for row in reversed(rows)]
    return {"count": len(records), "records": records}
