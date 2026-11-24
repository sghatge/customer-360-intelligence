# AEP learning and build roadmap

Time budget: 6–8 hours/week. Suggested cadence: 2 × 2-hour build blocks + 1 × 2–4-hour review/lab block.

| Week | Focus | Hands-on output | Exit criteria |
|---|---|---|---|
| 1 | AEP foundations, XDM, schemas, datasets | Profile and event contracts | Explain schema, dataset, identity namespace and profile |
| 2 | Identity graph and profile design | Identity map and merge policy | CRM ID, ECID and email are distinct; duplicate scenarios tested |
| 3 | Event ingestion and data quality | Event validator and mapping | Invalid event and missing required fields are rejected |
| 4 | Consent and governance | Consent model and enforcement tests | Opt-out blocks activation |
| 5 | Real-Time CDP segmentation | Cart-abandoned-60m and lapsed-90d segment specs | Entry, exit and evaluation criteria documented |
| 6 | Query Service concepts | SQL examples and query cost checklist | Avoid unbounded scans; define time/partition filters |
| 7 | Activation and downstream contracts | AJO-ready audience export contract | Audience eligibility and consent included |
| 8 | Capstone and portfolio demo | Customer 360 walkthrough and architecture | Reproducible demo, tests, limitations and README complete |

## Weekly deliverable discipline
1. Read the week's concept notes.
2. Implement one small artifact.
3. Add at least one positive and one negative test.
4. Record assumptions and platform dependencies.
5. Update README and evidence log.

## Access dependency
A real AEP sandbox is required to practice tenant-specific schema creation, dataset setup, ingestion, identity graph inspection, segmentation UI and Query Service execution. Until access exists, use the synthetic lab and clearly label simulations.