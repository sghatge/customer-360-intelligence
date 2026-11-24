# Phase 5 — Enterprise Customer Lifecycle Integration

## Objective
Keep the AEP, AJO and Salesforce labs independent while giving them a common, versioned event and action vocabulary. The shared contracts are duplicated into each repository so each lab can be exercised and versioned independently.

## End-to-end reference flow
1. **Salesforce → AEP:** CRM identity, profile attributes and consent preferences are represented in the AEP profile contract.
2. **AEP qualification:** Synthetic profile and event data qualify a customer for a scenario.
3. **AEP → AJO:** A lifecycle event carries a stable `correlationId`, customer CRM ID, journey context, channel consent and decision status.
4. **AJO orchestration:** The journey simulator checks entry conditions, consent, fatigue, wait, conversion exit and offer guardrails.
5. **AJO → Salesforce:** A journey outcome may propose a CRM follow-up action, with the same `correlationId` for traceability.
6. **Salesforce policy gate:** The CRM lab displays the inbound outcome and a proposed task. Human approval is required; no Salesforce write is executed.
7. **Salesforce → AEP feedback:** A production implementation would publish approved CRM outcome events back to AEP for measurement and future audience qualification.

## Shared contracts
- `contracts/customer-lifecycle-event.json` — common event envelope for audience qualification, journey entry, channel eligibility/block, conversion, exit and CRM follow-up events.
- `contracts/salesforce-followup-action.json` — constrained CRM action proposal. `requiresHumanApproval` must be true.
- Existing AEP profile and ExperienceEvent contracts remain the source learning contracts for profile and behavioural data.

## Correlation and idempotency
- Generate one correlation ID per customer journey instance.
- Preserve it across AEP qualification, AJO journey outcome and Salesforce task proposal.
- Use a separate unique event/request ID for each emitted event or action.
- In production, persist processed IDs and enforce idempotency at the integration service; this lab only demonstrates the keys and does not persist a distributed event ledger.

## Governance controls
- Consent values are explicit: `GRANTED`, `DENIED`, `UNKNOWN`.
- A channel decision must fail closed when consent is absent, denied or unknown.
- A CRM action remains `PENDING_HUMAN_APPROVAL` until an authorized reviewer approves it.
- Do not send messages or write CRM records from these simulators.
- Never use synthetic profile examples as real customer data.

## Smoke-test sequence
1. In AEP, select a profile with email and SMS consent and inspect the lifecycle event.
2. Select a channel for which consent is denied and confirm the event is `message_blocked`.
3. Download the lifecycle JSON and check its `correlationId`.
4. In AJO, open Integration contract and compare the event envelope.
5. In Salesforce, open AJO outcome inbox and verify the task remains `PENDING_HUMAN_APPROVAL`.
6. Evaluate the task with approval unchecked and checked; both actions are simulations only.
7. Confirm the same correlation ID is carried across the three lab applications.

## Production integration boundary
This phase creates shared contracts and local previews only. Real connectivity requires an approved integration service or event bus, authenticated service identities, secrets management, tenant-specific API permissions, retry/dead-letter handling, schema compatibility checks, observability, consent governance and end-to-end security testing. No AEP, AJO or Salesforce tenant is connected by this phase.
