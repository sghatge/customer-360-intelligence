"""Contract-first local integration gateway for the synthetic MarTech labs.

This service validates and records synthetic events in memory. It does not connect
to Adobe or Salesforce, send messages, or persist production data.
"""
from __future__ import annotations
import hmac
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
EVENT_SCHEMA = json.loads((ROOT / "contracts/customer-lifecycle-event.json").read_text())
ACTION_SCHEMA = json.loads((ROOT / "contracts/salesforce-followup-action.json").read_text())
event_validator = Draft202012Validator(EVENT_SCHEMA, format_checker=FormatChecker())
action_validator = Draft202012Validator(ACTION_SCHEMA, format_checker=FormatChecker())

app = FastAPI(title="MarTech Lifecycle Integration Gateway", version="0.1.0",
              description="Synthetic contract-validation gateway. No live Adobe/Salesforce connections.")
EVENTS: dict[str, dict[str, Any]] = {}
ACTIONS: dict[str, dict[str, Any]] = {}
AUDIT: list[dict[str, Any]] = []

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
    AUDIT.append({"auditId":str(uuid.uuid4()),"occurredAt":datetime.now(timezone.utc).isoformat(),
                  "action":action,"correlationId":correlation_id,"status":status,"detail":detail})

@app.get("/health")
def health() -> dict[str, str]:
    return {"status":"ok","mode":"synthetic_in_memory"}

@app.post("/v1/events", dependencies=[Depends(require_api_key)])
def ingest_event(payload: dict[str, Any]) -> dict[str, Any]:
    errors = schema_errors(event_validator, payload)
    if errors:
        audit("EVENT_VALIDATION", str(payload.get("correlationId","UNKNOWN")), "REJECTED", "; ".join(errors))
        raise HTTPException(status_code=422, detail={"contract":"customer-lifecycle-event","errors":errors})
    event_id = payload["eventId"]
    if event_id in EVENTS:
        audit("EVENT_INGEST", payload["correlationId"], "DUPLICATE", event_id)
        return {"status":"DUPLICATE_IGNORED","eventId":event_id,"correlationId":payload["correlationId"]}
    EVENTS[event_id] = payload
    audit("EVENT_INGEST", payload["correlationId"], "ACCEPTED", event_id)
    return {"status":"ACCEPTED","eventId":event_id,"correlationId":payload["correlationId"]}

@app.get("/v1/events/{correlation_id}", dependencies=[Depends(require_api_key)])
def get_events(correlation_id: str) -> dict[str, Any]:
    matches = [event for event in EVENTS.values() if event["correlationId"] == correlation_id]
    return {"correlationId":correlation_id,"count":len(matches),"events":matches}

@app.post("/v1/crm-actions", dependencies=[Depends(require_api_key)])
def propose_crm_action(payload: dict[str, Any]) -> dict[str, Any]:
    errors = schema_errors(action_validator, payload)
    if errors:
        audit("CRM_ACTION_VALIDATION", str(payload.get("correlationId","UNKNOWN")), "REJECTED", "; ".join(errors))
        raise HTTPException(status_code=422, detail={"contract":"salesforce-followup-action","errors":errors})
    if payload["requiresHumanApproval"] is not True or payload["status"] != "PENDING_HUMAN_APPROVAL":
        audit("CRM_ACTION_POLICY", payload["correlationId"], "REJECTED", "Human approval is mandatory")
        raise HTTPException(status_code=403, detail="CRM action must remain pending human approval")
    request_id = payload["requestId"]
    if request_id in ACTIONS:
        audit("CRM_ACTION", payload["correlationId"], "DUPLICATE", request_id)
        return {"status":"DUPLICATE_IGNORED","requestId":request_id}
    ACTIONS[request_id] = payload
    audit("CRM_ACTION", payload["correlationId"], "PENDING_HUMAN_APPROVAL", request_id)
    return {"status":"PENDING_HUMAN_APPROVAL","requestId":request_id,
            "correlationId":payload["correlationId"],"executed":False}

@app.get("/v1/audit", dependencies=[Depends(require_api_key)])
def get_audit(limit: int = 100) -> dict[str, Any]:
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 500")
    return {"count":min(limit,len(AUDIT)),"records":AUDIT[-limit:]}
