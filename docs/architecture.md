# AEP Customer 360 logical architecture

## Scope
This lab models AEP as the customer data foundation. It is not a substitute for tenant-specific Adobe solution design.

## Logical flow
Salesforce CRM + website/app events + commerce/order data → source mapping and validation → XDM-aligned datasets → identity namespaces and graph → Real-Time Customer Profile → audience definitions → consent-aware activation to AJO/destinations.

## Design principles
- Define XDM schema and field semantics before ingesting source tables.
- Separate profile attributes from time-series experience events.
- Preserve source identifiers and identity namespaces; do not collapse CRM ID, ECID and email into one field.
- Define identity stitching, merge policies, precedence and duplicate handling explicitly.
- Carry consent purpose, channel, status, source and effective time; downstream activation must evaluate the applicable consent.
- Use synthetic data in this repository.
- Query Service examples must use bounded time windows and selective columns; validate query cost in the actual tenant.

## Initial entities
- Person profile: CRM ID, ECID, email, name, loyalty tier, country, consent preferences.
- Experience event: event ID, event type, event timestamp, identity map, product/cart/order context.
- Consent record: subject identity, channel/purpose, status, source, captured/updated timestamps.

## Boundaries
AEP owns unified behavioural context, profile enrichment and audience membership in this design. Salesforce remains authoritative for CRM entities and agreed consent source fields. AJO owns journey execution and engagement history. Confirm actual ownership with the enterprise data owner before production integration.