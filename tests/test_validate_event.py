import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from validate_event import validate

def test_valid_event_passes():
    event = {"eventId":"E1","eventType":"addToCart","timestamp":"2026-11-24T08:00:00+05:30","identity":{"ecid":"X1"}}
    assert validate(event) == []

def test_missing_identity_fails():
    event = {"eventId":"E2","eventType":"purchase","timestamp":"2026-11-24T08:00:00Z","identity":{}}
    assert "identity must contain crmId, ecid or email" in validate(event)

def test_unknown_event_type_fails():
    event = {"eventId":"E3","eventType":"unsubscribeEverything","timestamp":"2026-11-24T08:00:00Z","identity":{"crmId":"C1"}}
    assert "eventType is not supported" in validate(event)
