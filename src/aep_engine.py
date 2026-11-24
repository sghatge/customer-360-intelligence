"""Deterministic learning rules for the synthetic AEP lab."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:  # clear runtime error when optional dependency is missing
    Draft202012Validator = None
    FormatChecker = None

ROOT = Path(__file__).resolve().parents[1]

def validate_against_contract(instance: dict[str, Any], contract_path: str) -> list[str]:
    if Draft202012Validator is None:
        raise RuntimeError("Install project dependencies: pip install -e .")
    schema = json.loads((ROOT / contract_path).read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [f"{'.'.join(str(p) for p in e.absolute_path) or '$'}: {e.message}"
            for e in sorted(validator.iter_errors(instance), key=lambda e: list(map(str, e.absolute_path)))]

def detect_identity_collisions(profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flag shared email across distinct CRM IDs; never auto-merge."""
    by_email: dict[str, list[dict[str, Any]]] = {}
    for profile in profiles:
        email = (profile.get("email") or "").strip().casefold()
        if email:
            by_email.setdefault(email, []).append(profile)
    collisions = []
    for email, records in by_email.items():
        crm_ids = sorted({p.get("crmId") for p in records if p.get("crmId")})
        if len(crm_ids) > 1:
            collisions.append({"email": email, "crm_ids": crm_ids,
                               "status": "REVIEW_REQUIRED", "action": "DO_NOT_AUTO_MERGE"})
    return collisions

def evaluate_audience(profile: dict[str, Any], events: list[dict[str, Any]],
                      channel: str, allowed_tiers: set[str], min_ltv: float,
                      max_recency_days: int) -> dict[str, Any]:
    """Return segment and consent decisions; channel consent is a hard gate."""
    if channel not in {"email", "sms"}:
        raise ValueError("channel must be 'email' or 'sms'")
    consent = (profile.get("consent") or {}).get(channel, "UNKNOWN")
    event_ids = {e.get("eventId") for e in events}
    segment_match = (
        profile.get("loyaltyTier") in allowed_tiers
        and float(profile.get("lifetimeValue", 0)) >= min_ltv
        and int(profile.get("lastSeenDays", 10**9)) <= max_recency_days
    )
    consent_eligible = consent == "GRANTED"
    return {
        "profile_id": profile.get("crmId"),
        "segment_match": segment_match,
        "consent_status": consent,
        "eligible": bool(segment_match and consent_eligible),
        "reason": "ELIGIBLE" if segment_match and consent_eligible else
                  "NOT_IN_SEGMENT" if not segment_match else "CONSENT_NOT_GRANTED",
        "matched_event_count": len(event_ids),
    }

def apply_entry_exit_rule(previously_in: bool, current_eligible: bool) -> str:
    """Simple deterministic membership transition, not Adobe segment evaluation."""
    if not previously_in and current_eligible:
        return "ENTER"
    if previously_in and not current_eligible:
        return "EXIT"
    return "REMAIN" if current_eligible else "NOT_IN_AUDIENCE"
