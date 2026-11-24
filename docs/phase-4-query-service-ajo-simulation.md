# Phase 4 — Query Service and AJO Journey Simulation

## Delivered in the learning lab

### Query Service practice workbench
- Adds an in-memory, read-only SQL workbench over the lab's synthetic `profiles` and `events` tables.
- Includes example queries for high-value opted-in profiles, cart events joined to customer details, event volume by type and inactive profiles.
- Allows one SELECT statement or read-only CTE per run.
- Rejects write/DDL/administrative statements through a SQLite authorizer and rejects multiple SQL statements.
- Caps displayed output at 100 rows.

**Important:** This is a SQLite-based learning simulator. It is not Adobe Experience Platform Query Service, does not reproduce Adobe SQL dialect/performance, and does not access AEP datasets.

### AEP → AJO journey hand-off
Three conceptual journey patterns are available:
- Abandoned cart recovery: cart event → illustrative wait → purchase re-check → consent/suppression re-check → message action preview.
- Post-purchase cross-sell: purchase event → illustrative wait → eligibility check → consent/suppression re-check → action preview.
- VIP engagement: loyalty qualification → engagement check → consent/suppression re-check → action preview.

The hand-off payload is marked `SIMULATED_NOT_SENT`. No AJO journey or message is created.

## Smoke-test checklist
1. Run each of the four supplied SQL examples.
2. Try `DELETE FROM profiles`; the workbench must reject it.
3. Try `SELECT 1; SELECT 2`; multiple statements must be rejected.
4. Build an audience in Audience Builder and open AJO Journey Preview.
5. Change the journey pattern and verify the entry trigger and steps update.
6. Confirm every journey payload remains `SIMULATED_NOT_SENT`.

## Production-readiness gap
A real integration requires licensed AEP and AJO sandboxes, approved identities and datasets, API credentials held in secrets management, destination configuration, consent governance, journey design and end-to-end QA. No credentials should be committed to this repository.
