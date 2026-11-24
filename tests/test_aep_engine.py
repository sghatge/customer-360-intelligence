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
