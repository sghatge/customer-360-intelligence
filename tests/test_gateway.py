from fastapi.testclient import TestClient
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gateway"))
import app as gateway

client = TestClient(gateway.app)
TOKEN = "test-gateway-key"

def setup_function():
    os.environ["GATEWAY_API_KEY"] = TOKEN
    os.environ["GATEWAY_DB_PATH"] = str(Path(__file__).parent / "test_gateway.sqlite")
    path = Path(os.environ["GATEWAY_DB_PATH"])
    if path.exists():
        path.unlink()
    gateway.init_db()

def teardown_function():
    path = Path(os.environ["GATEWAY_DB_PATH"])
    if path.exists():
        path.unlink()

def headers():
    return {"Authorization": f"Bearer {TOKEN}"}

def event(event_id="E-1"):
    return {
        "eventId": event_id, "correlationId": "CORR-C1-1",
        "occurredAt": "2026-11-24T08:00:00Z", "source": "AJO",
        "eventType": "message_blocked", "customer": {"crmId": "C1"},
        "journey": {"journeyId": "J1", "journeyName": "Cart recovery", "step": "consent", "channel": "SMS"},
        "consent": {"sms": "DENIED"}, "status": "BLOCKED", "reason": "SMS consent denied"
    }

def action():
    return {
        "requestId": "SF-1", "correlationId": "CORR-C1-1",
        "customer": {"crmId": "C1", "recordType": "Contact"},
        "actionType": "CREATE_TASK", "subject": "Review journey", "priority": "Normal",
        "status": "PENDING_HUMAN_APPROVAL", "requiresHumanApproval": True,
        "sourceJourney": "Cart recovery"
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

def test_event_and_audit_survive_app_module_reload():
    client.post("/v1/events", json=event(), headers=headers())
    import importlib
    importlib.reload(gateway)
    restarted_client = TestClient(gateway.app)
    result = restarted_client.get("/v1/events/CORR-C1-1", headers=headers())
    audit_result = restarted_client.get("/v1/audit", headers=headers())
    assert result.json()["count"] == 1
    assert audit_result.json()["records"][-1]["status"] == "ACCEPTED"

def test_retry_job_schedules_exponential_backoff():
    created = client.post("/v1/retries", json={
        "correlationId": "CORR-C1-1", "taskType": "AEP_EVENT_FORWARD",
        "payload": {"eventId": "E-1"}, "maxAttempts": 3
    }, headers=headers()).json()
    failed = client.post(f"/v1/retries/{created['jobId']}/fail",
                         json={"error": "temporary downstream outage"}, headers=headers()).json()
    assert failed["status"] == "RETRY_SCHEDULED"
    assert failed["attempts"] == 1
    assert failed["nextAttemptAt"] is not None
    listed = client.get("/v1/retries?status=RETRY_SCHEDULED", headers=headers()).json()
    assert listed["count"] == 1

def test_retry_job_moves_to_dead_letter_after_max_attempts():
    created = client.post("/v1/retries", json={
        "correlationId": "CORR-C1-2", "taskType": "AJO_OUTCOME_FORWARD",
        "payload": {"outcome": "FAILED"}, "maxAttempts": 2
    }, headers=headers()).json()
    first = client.post(f"/v1/retries/{created['jobId']}/fail",
                        json={"error": "temporary error"}, headers=headers()).json()
    second = client.post(f"/v1/retries/{created['jobId']}/fail",
                         json={"error": "still failing"}, headers=headers()).json()
    assert first["status"] == "RETRY_SCHEDULED"
    assert second["status"] == "DEAD_LETTER"
    assert second["nextAttemptAt"] is None
    dead = client.get("/v1/retries?status=DEAD_LETTER", headers=headers()).json()
    assert dead["count"] == 1

def test_retry_rejects_invalid_max_attempts():
    response = client.post("/v1/retries", json={
        "correlationId": "C", "taskType": "TEST", "payload": {}, "maxAttempts": 99
    }, headers=headers())
    assert response.status_code == 422
