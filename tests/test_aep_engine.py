import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aep_engine import (validate_against_contract, detect_identity_collisions,
                        evaluate_audience, apply_entry_exit_rule)

def test_event_contract_accepts_valid_event():
    event = {"eventId":"E1","eventType":"addToCart","timestamp":"2026-11-24T08:00:00+05:30",
             "identity":{"ecid":"X1"},"commerce":{"currency":"INR","value":1200}}
    assert validate_against_contract(event, "contracts/experience-event.json") == []

def test_event_contract_rejects_invalid_currency_and_unknown_field():
    event = {"eventId":"E1","eventType":"purchase","timestamp":"2026-11-24T08:00:00Z",
             "identity":{"crmId":"C1"},"commerce":{"currency":"rupees","value":10},
             "unexpected":"not allowed"}
    errors = validate_against_contract(event, "contracts/experience-event.json")
    assert any("currency" in error for error in errors)
    assert any("unexpected" in error for error in errors)

def test_profile_contract_requires_consent():
    profile = {"crmId":"C1","country":"IN"}
    errors = validate_against_contract(profile, "contracts/profile.json")
    assert any("consent" in error for error in errors)

def test_shared_email_across_customers_is_flagged_not_merged():
    profiles = [{"crmId":"C1","email":"shared@example.test"},
                {"crmId":"C2","email":"SHARED@example.test"}]
    result = detect_identity_collisions(profiles)
    assert result[0]["status"] == "REVIEW_REQUIRED"
    assert result[0]["action"] == "DO_NOT_AUTO_MERGE"

def test_same_email_for_same_crm_id_is_not_collision():
    profiles = [{"crmId":"C1","email":"a@example.test"},
                {"crmId":"C1","email":"a@example.test"}]
    assert detect_identity_collisions(profiles) == []

def test_consent_denial_blocks_audience_eligibility():
    profile = {"crmId":"C1","loyaltyTier":"GOLD","lifetimeValue":50000,
               "lastSeenDays":2,"consent":{"email":"DENIED"}}
    result = evaluate_audience(profile, [], "email", {"GOLD"}, 10000, 30)
    assert result["segment_match"] is True
    assert result["eligible"] is False
    assert result["reason"] == "CONSENT_NOT_GRANTED"

def test_membership_entry_and_exit_transitions():
    assert apply_entry_exit_rule(False, True) == "ENTER"
    assert apply_entry_exit_rule(True, False) == "EXIT"
    assert apply_entry_exit_rule(True, True) == "REMAIN"
    assert apply_entry_exit_rule(False, False) == "NOT_IN_AUDIENCE"

from aep_engine import run_read_only_sql

def test_read_only_sql_returns_synthetic_profile_rows():
    profiles = [{"crm_id":"C1","name":"A","email":"a@example.test","ecid":"X1","tier":"GOLD","ltv":50000,"email_ok":1,"sms_ok":0,"last_seen":2}]
    result = run_read_only_sql("SELECT crm_id, tier FROM profiles WHERE ltv > 10000", profiles, [])
    assert result["row_count"] == 1
    assert result["rows"][0]["tier"] == "GOLD"

def test_read_only_sql_rejects_delete():
    try:
        run_read_only_sql("DELETE FROM profiles", [], [])
    except ValueError as exc:
        assert "Only SELECT" in str(exc)
    else:
        raise AssertionError("DELETE should be rejected")

def test_read_only_sql_rejects_multiple_statements():
    try:
        run_read_only_sql("SELECT 1; SELECT 2", [], [])
    except ValueError:
        pass
    else:
        raise AssertionError("multiple statements should be rejected")

from aep_engine import validate_against_contract

def test_shared_lifecycle_event_contract_accepts_correlated_ajo_outcome():
    event = {
        "eventId":"LCE-CORR-C1-001",
        "correlationId":"CORR-C1-001",
        "occurredAt":"2026-11-24T08:00:00Z",
        "source":"AJO",
        "eventType":"message_blocked",
        "customer":{"crmId":"C1"},
        "journey":{"journeyId":"J1","journeyName":"Cart recovery","step":"channel_decision","channel":"SMS"},
        "consent":{"sms":"DENIED"},
        "status":"BLOCKED",
        "reason":"SMS consent denied"
    }
    assert validate_against_contract(event, "contracts/customer-lifecycle-event.json") == []

def test_salesforce_followup_contract_requires_human_approval():
    request = {
        "requestId":"SF-CORR-C1-001",
        "correlationId":"CORR-C1-001",
        "customer":{"crmId":"C1","recordType":"Contact"},
        "actionType":"CREATE_TASK",
        "subject":"Review journey outcome",
        "priority":"Normal",
        "status":"PENDING_HUMAN_APPROVAL",
        "requiresHumanApproval":True,
        "sourceJourney":"Cart recovery"
    }
    assert validate_against_contract(request, "contracts/salesforce-followup-action.json") == []
    request["requiresHumanApproval"] = False
    assert validate_against_contract(request, "contracts/salesforce-followup-action.json")
