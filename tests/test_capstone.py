import pytest

from capstone import build_customer_360_capstone
from aep_engine import validate_against_contract


PROFILE_EMAIL_SMS = {
    "crm_id": "C-1001",
    "name": "Aarav Mehta",
    "email": "aarav@example.test",
    "ecid": "ECID-9001",
    "email_ok": True,
    "sms_ok": True,
}
EVENTS = [
    {"event_id": "EV-01", "crm_id": "C-1001", "event_type": "add_to_cart"},
    {"event_id": "EV-02", "crm_id": "C-1001", "event_type": "purchase"},
]


def test_email_cart_journey_is_eligible_and_contract_valid():
    result = build_customer_360_capstone(
        PROFILE_EMAIL_SMS, EVENTS, "Abandoned cart recovery", "EMAIL",
        occurred_at="2026-11-24T09:00:00+05:30",
    )
    assert result["eligible"] is True
    assert result["decision"] == "ELIGIBLE"
    assert result["matched_event_count"] == 1
    assert result["execution_performed"] is False
    assert validate_against_contract(result["lifecycle_event"], "contracts/customer-lifecycle-event.json") == []
    assert validate_against_contract(result["salesforce_action"], "contracts/salesforce-followup-action.json") == []


def test_sms_consent_denial_blocks_journey_entry():
    profile = {**PROFILE_EMAIL_SMS, "sms_ok": False}
    result = build_customer_360_capstone(
        profile, EVENTS, "Post-purchase follow-up", "SMS",
        occurred_at="2026-11-24T09:00:00+05:30",
    )
    assert result["eligible"] is False
    assert result["decision"] == "CONSENT_NOT_GRANTED"
    assert result["timeline"][3]["status"] == "ENTRY_BLOCKED"


def test_missing_trigger_event_blocks_journey():
    result = build_customer_360_capstone(
        PROFILE_EMAIL_SMS, [], "Abandoned cart recovery", "EMAIL",
        occurred_at="2026-11-24T09:00:00+05:30",
    )
    assert result["eligible"] is False
    assert result["decision"] == "TRIGGER_EVENT_NOT_FOUND"


def test_unknown_consent_fails_closed():
    profile = {**PROFILE_EMAIL_SMS, "email_ok": None}
    result = build_customer_360_capstone(
        profile, EVENTS, "Abandoned cart recovery", "EMAIL",
        occurred_at="2026-11-24T09:00:00+05:30",
    )
    assert result["eligible"] is False
    assert result["consent_status"] == "UNKNOWN"


def test_profile_qualification_journey_does_not_require_event():
    result = build_customer_360_capstone(
        PROFILE_EMAIL_SMS, [], "VIP service follow-up", "EMAIL",
        occurred_at="2026-11-24T09:00:00+05:30",
    )
    assert result["eligible"] is True
    assert result["trigger_met"] is True


def test_invalid_channel_is_rejected():
    with pytest.raises(ValueError, match="Channel"):
        build_customer_360_capstone(
            PROFILE_EMAIL_SMS, EVENTS, "Abandoned cart recovery", "PUSH"
        )


def test_action_always_requires_human_approval():
    result = build_customer_360_capstone(
        PROFILE_EMAIL_SMS, EVENTS, "Abandoned cart recovery", "EMAIL",
        occurred_at="2026-11-24T09:00:00+05:30",
    )
    assert result["salesforce_action"]["requiresHumanApproval"] is True
    assert result["salesforce_action"]["status"] == "PENDING_HUMAN_APPROVAL"
