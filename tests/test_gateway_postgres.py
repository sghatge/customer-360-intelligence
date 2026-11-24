"""PostgreSQL integration smoke tests; enabled when GATEWAY_TEST_POSTGRES_URL is set."""
import os

import pytest

POSTGRES_URL = os.getenv("GATEWAY_TEST_POSTGRES_URL")
if not POSTGRES_URL:
    pytest.skip("GATEWAY_TEST_POSTGRES_URL is not configured", allow_module_level=True)

os.environ["GATEWAY_DATABASE_URL"] = POSTGRES_URL
os.environ["GATEWAY_API_KEY"] = "postgres-ci-test-key"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from gateway import app as gateway

client = TestClient(gateway.app)
HEADERS = {"Authorization": "Bearer postgres-ci-test-key"}

@pytest.fixture(autouse=True)
def clean_database():
    gateway.init_db()
    engine = create_engine(gateway.database_url())
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM audit"))
        conn.execute(text("DELETE FROM crm_actions"))
        conn.execute(text("DELETE FROM events"))
    yield
    engine.dispose()

def sample_event():
    return {
        "eventId": "PG-EVENT-1", "correlationId": "PG-CORR-1",
        "occurredAt": "2026-11-24T08:00:00Z", "source": "AJO",
        "eventType": "message_blocked", "customer": {"crmId": "PG-C1"},
        "journey": {"journeyId": "J1", "journeyName": "Cart recovery", "step": "consent", "channel": "SMS"},
        "consent": {"sms": "DENIED"}, "status": "BLOCKED", "reason": "SMS consent denied"
    }

def test_postgres_health_reports_postgresql():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["storage"] == "postgresql"

def test_postgres_event_persistence_idempotency_and_audit():
    first = client.post("/v1/events", json=sample_event(), headers=HEADERS)
    duplicate = client.post("/v1/events", json=sample_event(), headers=HEADERS)
    lookup = client.get("/v1/events/PG-CORR-1", headers=HEADERS)
    audit = client.get("/v1/audit", headers=HEADERS)
    assert first.json()["status"] == "ACCEPTED"
    assert duplicate.json()["status"] == "DUPLICATE_IGNORED"
    assert lookup.json()["count"] == 1
    assert any(row["status"] == "ACCEPTED" for row in audit.json()["records"])
