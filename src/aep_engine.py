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

def assess_identity_conflicts(profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flag shared ECID or email values across CRM IDs; never auto-merge.

    This is a conservative lab rule, not Adobe Identity Service graph logic.
    CRM ID remains the record key; ambiguous shared identifiers require review.
    """
    conflicts: list[dict[str, Any]] = []
    for namespace, field in (("ECID", "ecid"), ("EMAIL", "email")):
        by_value: dict[str, set[str]] = {}
        for profile in profiles:
            value = (profile.get(field) or "").strip()
            crm_id = (profile.get("crmId") or profile.get("crm_id") or "").strip()
            if value and crm_id:
                normalized = value.casefold() if namespace == "EMAIL" else value
                by_value.setdefault(normalized, set()).add(crm_id)
        for value, crm_ids in sorted(by_value.items()):
            if len(crm_ids) > 1:
                conflicts.append({
                    "namespace": namespace,
                    "identifier": value,
                    "crm_ids": sorted(crm_ids),
                    "status": "REVIEW_REQUIRED",
                    "action": "DO_NOT_AUTO_MERGE",
                })
    return conflicts

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

def run_read_only_sql(query: str, profiles: list[dict[str, Any]],
                      events: list[dict[str, Any]], max_rows: int = 100) -> dict[str, Any]:
    """Execute a single read-only SELECT/WITH query over in-memory synthetic tables."""
    import sqlite3
    statement = query.strip()
    if not statement or not statement.lower().startswith(("select", "with")):
        raise ValueError("Only SELECT queries and read-only CTEs are allowed.")
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    try:
        pcols = ["crm_id","name","email","ecid","tier","ltv","email_ok","sms_ok","last_seen"]
        ecols = ["event_id","crm_id","ecid","event_type","product","event_time"]
        connection.execute("CREATE TABLE profiles (crm_id TEXT, name TEXT, email TEXT, ecid TEXT, tier TEXT, ltv REAL, email_ok INTEGER, sms_ok INTEGER, last_seen INTEGER)")
        connection.execute("CREATE TABLE events (event_id TEXT, crm_id TEXT, ecid TEXT, event_type TEXT, product TEXT, event_time TEXT)")
        connection.executemany(
            "INSERT INTO profiles VALUES (?,?,?,?,?,?,?,?,?)",
            [tuple(int(p.get(k, 0)) if k in {"email_ok","sms_ok"} else p.get(k) for k in pcols) for p in profiles]
        )
        connection.executemany(
            "INSERT INTO events VALUES (?,?,?,?,?,?)",
            [tuple(e.get(k) for k in ecols) for e in events]
        )
        allowed = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION}
        if hasattr(sqlite3, "SQLITE_RECURSIVE"):
            allowed.add(sqlite3.SQLITE_RECURSIVE)
        def authorize(action, arg1, arg2, database, trigger):
            return sqlite3.SQLITE_OK if action in allowed else sqlite3.SQLITE_DENY
        connection.set_authorizer(authorize)
        connection.set_progress_handler(lambda: 1, 100000)
        cursor = connection.execute(statement)
        rows = cursor.fetchmany(max_rows + 1)
        truncated = len(rows) > max_rows
        rows = rows[:max_rows]
        return {"columns":[d[0] for d in cursor.description or []],
                "rows":[dict(row) for row in rows],"truncated":truncated,
                "row_count":len(rows)}
    except sqlite3.Error as exc:
        raise ValueError(f"SQL rejected or invalid: {exc}") from exc
    finally:
        connection.close()
