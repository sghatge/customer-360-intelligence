# AEP Customer 360 Intelligence Lab

Hands-on learning project for Adobe Experience Platform (AEP), XDM, identity resolution, Real-Time Customer Profile, Real-Time CDP audiences, consent and Query Service.

> Learning lab only. Uses synthetic data and platform-neutral contracts until an Adobe sandbox is available. It does not claim to connect to a live AEP tenant.

## Business outcome
Build a trustworthy unified customer profile from CRM, web and commerce signals, then define audiences that can be activated by downstream engagement platforms.

## Architecture
1. Source systems: Salesforce CRM, web/app events and commerce transactions.
2. Ingestion contracts: source-to-XDM mapping, schema validation and consent metadata.
3. Identity: CRM ID, ECID and normalized email as separate identity signals; never use email as the only identity key.
4. Profile: resolve profile attributes and event history with explicit merge/ownership rules.
5. Audience: evaluate illustrative segments such as cart-abandoned-60m and lapsed-90d.
6. Activation: publish eligible audience membership to AJO or approved destinations only after consent and governance checks.

## Repository map
- `docs/architecture.md` — logical design and data flow
- `docs/field-ownership.md` — source-of-truth and field stewardship
- `docs/lab-01-profile-foundation.md` — first hands-on exercise
- `contracts/` — platform-neutral profile and event contracts
- `data/` — synthetic sample records only
- `src/` — local validation utilities
- `tests/` — deterministic checks
- `sql/` — read-only learning queries
- `docs/phase-4-query-service-ajo-simulation.md` — Query Service and journey hand-off guide
- `ROADMAP.md` — 8-week plan at 6–8 hours/week

## Quick start
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -e .[dev]
pytest
python src/validate_event.py data/events.jsonl
```

## Learning sequence
XDM concepts → profile and identity design → event ingestion contracts → consent → segment logic → Query Service concepts and cost controls → AJO journey hand-off simulation → activation readiness.

## Query Service and AJO simulation
The Streamlit lab includes a local read-only SQL workbench over synthetic data and a conceptual AEP-to-AJO journey preview. These are learning simulations, not Adobe service connections. See `docs/phase-4-query-service-ajo-simulation.md`.

## Enterprise lifecycle integration
The AEP, AJO and Salesforce labs share versioned `contracts/customer-lifecycle-event.json` and `contracts/salesforce-followup-action.json` contracts. The AEP app includes a Lifecycle Integration Hub to preview correlated events and human-approved CRM action proposals. See `docs/enterprise-lifecycle-integration.md`. This is a local synthetic simulation, not a live connector.

## Data safety
Never commit client data, production exports, credentials, access tokens or identifiable customer records. Use synthetic examples only. Keep secrets in environment variables and `.env` must remain ignored.

## Source material
Adapted from the user's Google Drive document **Adobe, AEP, AJO & Salesforce - Consolidated Guide** and **MarTech 2030 - Governed AI Agent Architecture**. Platform-specific deployment steps must be verified against the licensed tenant and current Adobe documentation.