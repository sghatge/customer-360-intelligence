from fastapi.testclient import TestClient
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gateway"))
import app as gateway

client = TestClient(gateway.app)
TOKEN = "test-gateway-key"

def setup_function():
    gateway.EVENTS.clear()
    gateway.ACTIONS.clear()
    gateway.AUDIT.clear()
    os.environ["GATEWAY_API_KEY"] = TOKEN

def headers():
    return {"Authorization":f"Bearer {TOKEN}"}

def event(event_id="E-1"):
    return {
        "eventId":event_id,"correlationId":"CORR-C1-1",
        "occurredAt":"2026-11-24T08:00:00Z","source":"AJO",
        "eventType":"message_blocked","customer":{"crmId":"C1"},
        "journey":{"journeyId":"J1","journeyName":"Cart recovery","step":"consent","channel":"SMS"},
        "consent":{"sms":"DENIED"},"status":"BLOCKED","reason":"SMS consent denied"
    }

def action():
    return {
        "requestId":"SF-1","correlationId":"CORR-C1-1",
        "customer":{"crmId":"C1","recordType":"Contact"},
        "actionType":"CREATE_TASK","subject":"Review journey","priority":"Normal",
        "status":"PENDING_HUMAN_APPROVAL","requiresHumanApproval":True,
        "sourceJourney":"Cart recovery"
    }

def test_health_is_public():
    assert client.get("/health").json()["status"] == "ok"

def test_event_requires_api_key():
    assert client.post("/v1/events", json=event()).status_code == 401

def test_event_contract_validates_and_ingests():
    response = client.post("/v1/events", json=event(), headers=headers())
    assert response.status_code == 200
    assert response.json()["status"] == "ACCEPTED"

def test_duplicate_event_is_idempotently_ignored():
    client.post("/v1/events", json=event(), headers=headers())
    response = client.post("/v1/events", json=event(), headers=headers())
    assert response.json()["status"] == "DUPLICATE_IGNORED"

def test_invalid_event_is_rejected():
    bad = event()
    bad["customer"] = {}
    assert client.post("/v1/events", json=bad, headers=headers()).status_code == 422

def test_correlation_lookup_returns_event():
    client.post("/v1/events", json=event(), headers=headers())
    response = client.get("/v1/events/CORR-C1-1", headers=headers())
    assert response.json()["count"] == 1

def test_crm_action_stays_pending_and_is_not_executed():
    response = client.post("/v1/crm-actions", json=action(), headers=headers())
    assert response.status_code == 200
    assert response.json()["status"] == "PENDING_HUMAN_APPROVAL"
    assert response.json()["executed"] is False

def test_crm_action_cannot_bypass_approval():
    bad = action()
    bad["requiresHumanApproval"] = False
    assert client.post("/v1/crm-actions", json=bad, headers=headers()).status_code == 422

def test_audit_trail_records_accepted_event():
    client.post("/v1/events", json=event(), headers=headers())
    records = client.get("/v1/audit", headers=headers()).json()["records"]
    assert records[-1]["action"] == "EVENT_INGEST"
    assert records[-1]["status"] == "ACCEPTED"
