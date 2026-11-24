# Phase 2 — Interactive Customer Intelligence

## Scope delivered in the Streamlit lab

The application now includes six learning modules:

1. **Profile explorer** — inspect synthetic customer attributes, channel consent and associated events; inspect an XDM-inspired profile payload.
2. **Identity graph** — visualize the relationship between CRM ID, ECID, email and a unified profile. The diagram is illustrative, not a live Adobe identity graph.
3. **Audience builder** — filter synthetic profiles by loyalty tier, lifetime value and recency; evaluate email or SMS consent after segment matching; download the eligible sample as CSV.
4. **XDM schema explorer** — search a compact field catalogue with illustrative types, purpose and design notes.
5. **Event ingestion lab** — validate required identifiers, event type, timestamp and duplicate event ID; accepted records are stored in Streamlit session state only.
6. **Activation preview** — inspect a simulated hand-off contract for Adobe Journey Optimizer and Salesforce. No downstream activation occurs.

## Data and safety boundaries

- All records are fabricated learning examples using `.test` email addresses.
- No Adobe tenant, API, production dataset, customer data or destination is connected.
- The event simulator is session-scoped and does not persist or transmit events.
- The audience CSV is generated from synthetic profiles only.
- The activation preview is a contract illustration, not an export or send.

## Manual smoke-test checklist

- [ ] Open each of the six tabs on desktop and mobile.
- [ ] Select each customer and confirm profile details and event history.
- [ ] Switch identity graph profiles and verify all three identifiers change.
- [ ] Build an email audience and confirm opted-out profiles are excluded.
- [ ] Switch to SMS and confirm SMS consent drives eligibility.
- [ ] Search the XDM field catalogue.
- [ ] Submit a valid event, then attempt a duplicate event ID.
- [ ] Submit an invalid timestamp and confirm validation feedback.
- [ ] Download the eligible audience CSV.
- [ ] Confirm activation preview remains marked SIMULATED_NOT_SENT.

## Next milestone

The next development milestone is to strengthen the lab with formal schema validation against versioned JSON Schema contracts, explicit identity collision scenarios, audience entry/exit logic and a reproducible test suite. Real AEP tenant exercises remain gated on sandbox access.
