# Sprint 4 — AEP Customer 360 end-to-end capstone

## Objective

Demonstrate one synthetic customer journey across the AEP, Real-Time CDP,
Adobe Journey Optimizer and Salesforce concepts already represented in this
repository. This is a deterministic learning simulation, not a live Adobe or
Salesforce integration.

## Walkthrough

1. Resolve a synthetic customer using CRM ID and ECID.
2. Find the journey trigger in the customer's ExperienceEvent history.
3. Evaluate the requested channel against explicit consent.
4. Simulate RTCDP audience eligibility and AJO journey entry or block.
5. Emit a correlated lifecycle event using
   `contracts/customer-lifecycle-event.json`.
6. Prepare a Salesforce follow-up task proposal using
   `contracts/salesforce-followup-action.json`; the request always requires
   human approval.

## Supported scenarios

- Abandoned cart recovery — requires an `add_to_cart` event.
- Post-purchase follow-up — requires a `purchase` event.
- VIP service follow-up — profile-qualification trigger; no event trigger.

Channels: EMAIL, SMS and NONE. EMAIL and SMS fail closed unless the matching
profile consent value is explicitly true. NONE is a no-message control path.

## Evidence and safety

- Timeline shows profile resolution, event trigger, audience/consent decision,
  AJO entry decision and Salesforce follow-up proposal.
- Lifecycle event and Salesforce proposal are validated against the shared
  JSON Schema contracts in the repository.
- Correlation ID ties the lifecycle event and follow-up request together.
- Salesforce request remains `PENDING_HUMAN_APPROVAL`.
- `execution_performed` is always false; no message or CRM write is executed.
- All records are synthetic and session-local.

## Local validation

~~~bash
pytest -q tests/test_capstone.py
pytest -q
~~~

## Portfolio demonstration

Use the Streamlit **Customer 360 Capstone** tab to select a customer, journey
pattern and channel. Demonstrate both a consent-granted journey and a blocked
journey, then download the correlated lifecycle event and Salesforce review
proposal. The two JSON artifacts form a compact evidence pack for the demo.
