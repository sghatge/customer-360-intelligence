"""Small local validator for the synthetic AEP event contract."""
import json
import sys
from datetime import datetime
from pathlib import Path

ALLOWED_EVENTS = {"productView", "addToCart", "checkoutStart", "purchase"}

def validate(event: dict) -> list[str]:
    errors = []
    for field in ("eventId", "eventType", "timestamp", "identity"):
        if not event.get(field):
            errors.append(f"missing required field: {field}")
    if event.get("eventType") not in ALLOWED_EVENTS:
        errors.append("eventType is not supported")
    identity = event.get("identity") or {}
    if not any(identity.get(k) for k in ("crmId", "ecid", "email")):
        errors.append("identity must contain crmId, ecid or email")
    if event.get("timestamp"):
        try:
            datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
        except ValueError:
            errors.append("timestamp must be ISO-8601")
    return errors

def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "data/events.jsonl")
    failed = 0
    for line_no, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
            errors = validate(event)
        except (json.JSONDecodeError, TypeError) as exc:
            errors = [f"invalid JSON/event: {exc}"]
        status = "PASS" if not errors else "FAIL"
        print(f"{status} line {line_no}: " + ("valid event" if not errors else "; ".join(errors)))
        failed += bool(errors)
    return 1 if failed else 0

if __name__ == "__main__":
    raise SystemExit(main())