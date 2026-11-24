# Phase 3 — Enterprise AEP Simulation

## Delivered capabilities

### 1. Versioned JSON Schema validation
- The repository's `contracts/experience-event.json` and `contracts/profile.json` remain the source contracts for this lab.
- `src/aep_engine.py` validates JSON payloads against JSON Schema Draft 2020-12 and checks standard formats.
- Unknown fields are rejected by the current contracts where `additionalProperties` is false.
- The app's enterprise rule engine tab provides an interactive ExperienceEvent contract check.

### 2. Identity collision review
- Email values are normalized for case and whitespace before collision detection.
- A shared email across distinct CRM IDs is marked `REVIEW_REQUIRED`.
- The engine explicitly returns `DO_NOT_AUTO_MERGE`; it does not merge profile records.
- This is a conservative lab control, not a reproduction of Adobe's identity graph algorithm.

### 3. Audience eligibility and membership
- Segment matching checks loyalty tier, lifetime value and last-seen recency.
- Email/SMS consent must be explicitly `GRANTED`; `DENIED` and `UNKNOWN` are ineligible.
- Membership transitions are deterministic: `ENTER`, `EXIT`, `REMAIN`, `NOT_IN_AUDIENCE`.
- The transition helper is a teaching model, not Adobe Real-Time CDP's native streaming/batch segment evaluation.

### 4. Automated tests
The tests cover valid/invalid event contracts, required profile consent, identity collision detection, consent gating and membership transitions.

## Run locally

```bash
pip install -e .[dev]
pytest -q
streamlit run app.py
```

## Smoke tests in the app
1. Open **Enterprise rule engine**.
2. Validate the default event payload; it should pass.
3. Add an unknown property or malformed currency; validation should fail.
4. Review the shared-email scenario; it must show `REVIEW_REQUIRED` and `DO_NOT_AUTO_MERGE`.
5. Toggle prior membership and current eligibility to observe each transition.

## Limitations and next steps
- The contracts are project-specific teaching contracts, not Adobe-published XDM schema exports.
- No Adobe tenant, AEP API, dataset, identity graph, Query Service or destination is connected.
- Next: test profile contract payloads in the UI, add duplicate event/idempotency tests, model audience entry/exit with event windows, and prepare an AEP sandbox execution workbook.
