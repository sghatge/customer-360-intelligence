# Lab 01 — Define a customer profile foundation

## Objective
Design a minimal, governed customer profile and event contract before attempting ingestion.

## Steps
1. Review `contracts/profile.json` and `contracts/experience-event.json`.
2. Map each field to its source and business definition in `docs/field-ownership.md`.
3. Identify required fields, optional fields, types, identity namespaces and consent semantics.
4. Inspect the synthetic examples in `data/`.
5. Run the local event validator and tests.
6. Add one invalid event (missing eventType or identity) and confirm it fails.
7. Document how anonymous ECID activity becomes associated with a known CRM profile without treating email as the only key.

## Evidence to capture
- Annotated profile and event contracts.
- Source-to-target mapping table.
- Test output for valid and invalid events.
- One-page explanation of identity graph and merge-policy decisions.

## Definition of done
A reviewer can understand the profile, identify field owners, see consent boundaries and reproduce the local validation tests. No live Adobe tenant operation is implied by this lab.