"""Deterministic, synthetic AEP Customer 360 capstone journey builder."""
from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any


JOURNEYS = {
    "Abandoned cart recovery": {
        "journey_id": "JRN-CAPSTONE-CART-001",
        "trigger": "add_to_cart",
        "task_subject": "Review abandoned-cart journey outcome",
    },
    "Post-purchase follow-up": {
        "journey_id": "JRN-CAPSTONE-POSTPURCHASE-001",
        "trigger": "purchase",
        "task_subject": "Review post-purchase follow-up",
    },
    "VIP service follow-up": {
        "journey_id": "JRN-CAPSTONE-VIP-001",
        "trigger": "profile_qualification",
        "task_subject": "Review VIP customer follow-up",
    },
}


def build_customer_360_capstone(
    profile: dict[str, Any],
    events: list[dict[str, Any]],
    journey_name: str,
    channel: str,
    *,
    occurred_at: str | None = None,
) -> dict[str, Any]:
    """Build a consent-aware, contract-ready lifecycle simulation.

    No network calls or external writes are performed. Salesforce work is
    represented only as a human-review proposal.
    """
    if journey_name not in JOURNEYS:
        raise ValueError("Unsupported journey scenario.")
    if channel not in {"EMAIL", "SMS", "NONE"}:
        raise ValueError("Channel must be EMAIL, SMS or NONE.")

    crm_id = profile.get("crm_id")
    if not isinstance(crm_id, str) or not crm_id.strip():
        raise ValueError("A customer CRM ID is required.")

    journey = JOURNEYS[journey_name]
    consent_field = {"EMAIL": "email_ok", "SMS": "sms_ok"}.get(channel)
    consent_value = True if channel == "NONE" else profile.get(consent_field)
    consent_status = (
        "GRANTED" if consent_value is True else
        "DENIED" if consent_value is False else
        "UNKNOWN"
    )
    channel_allowed = channel == "NONE" or consent_value is True

    customer_events = [
        event for event in events
        if event.get("crm_id") == crm_id
    ]
    matched_events = [
        event for event in customer_events
        if event.get("event_type") == journey["trigger"]
    ]
    trigger_met = journey["trigger"] == "profile_qualification" or bool(matched_events)
    eligible = bool(channel_allowed and trigger_met)

    reason = (
        "ELIGIBLE" if eligible else
        "CONSENT_NOT_GRANTED" if not channel_allowed else
        "TRIGGER_EVENT_NOT_FOUND"
    )
    now = occurred_at or datetime.now(timezone.utc).isoformat()
    if not re.search(r"(Z|[+-]\d{2}:\d{2})$", now):
        raise ValueError("occurred_at must include a timezone.")

    correlation_id = f"CORR-{crm_id}-{journey['journey_id']}"
    event_payload = {
        "eventId": f"LCE-{correlation_id}",
        "correlationId": correlation_id,
        "occurredAt": now,
        "source": "INTEGRATION_SIMULATOR",
        "eventType": "message_eligible" if eligible else "message_blocked",
        "customer": {
            "crmId": crm_id,
            "ecid": profile.get("ecid"),
            "email": profile.get("email"),
        },
        "journey": {
            "journeyId": journey["journey_id"],
            "journeyName": journey_name,
            "step": "channel_decision",
            "channel": channel,
        },
        "consent": {
            "email": (
                "GRANTED" if profile.get("email_ok") is True else
                "DENIED" if profile.get("email_ok") is False else "UNKNOWN"
            ),
            "sms": (
                "GRANTED" if profile.get("sms_ok") is True else
                "DENIED" if profile.get("sms_ok") is False else "UNKNOWN"
            ),
        },
        "status": "ELIGIBLE" if eligible else "BLOCKED",
        "reason": reason,
        "metrics": {"currency": "INR"},
    }

    action_payload = {
        "requestId": f"SF-{correlation_id}",
        "correlationId": correlation_id,
        "customer": {"crmId": crm_id, "recordType": "Contact"},
        "actionType": "CREATE_TASK",
        "subject": journey["task_subject"],
        "description": (
            f"Review {journey_name} outcome. Channel decision: {reason}. "
            "Do not contact the customer until consent and channel policy are verified."
        ),
        "priority": "Normal",
        "status": "PENDING_HUMAN_APPROVAL",
        "requiresHumanApproval": True,
        "sourceJourney": journey["journey_id"],
    }

    timeline = [
        {
            "stage": "AEP · Customer profile",
            "status": "PROFILE_RESOLVED",
            "detail": f"Resolved synthetic profile {crm_id} with CRM ID and ECID.",
        },
        {
            "stage": "AEP · Experience event",
            "status": "TRIGGER_MET" if trigger_met else "TRIGGER_NOT_FOUND",
            "detail": (
                f"Found {len(matched_events)} matching {journey['trigger']} event(s)."
                if trigger_met else
                f"No {journey['trigger']} event found for this customer."
            ),
        },
        {
            "stage": "RTCDP · Audience and consent",
            "status": "ELIGIBLE" if eligible else "BLOCKED",
            "detail": f"Channel {channel}; consent {consent_status}; decision {reason}.",
        },
        {
            "stage": "AJO · Journey decision",
            "status": "SIMULATED_ENTRY" if eligible else "ENTRY_BLOCKED",
            "detail": (
                "Journey entry is simulated; no message is sent."
                if eligible else
                "Journey entry is blocked; no message is sent."
            ),
        },
        {
            "stage": "Salesforce · Follow-up proposal",
            "status": "PENDING_HUMAN_APPROVAL",
            "detail": "A task proposal is prepared; no Salesforce record is created.",
        },
    ]

    return {
        "customer": {
            "crm_id": crm_id,
            "name": profile.get("name"),
            "ecid": profile.get("ecid"),
            "email": profile.get("email"),
        },
        "journey": journey_name,
        "channel": channel,
        "trigger": journey["trigger"],
        "trigger_met": trigger_met,
        "consent_status": consent_status,
        "eligible": eligible,
        "decision": reason,
        "matched_event_count": len(matched_events),
        "timeline": timeline,
        "lifecycle_event": event_payload,
        "salesforce_action": action_payload,
        "execution_performed": False,
    }
