# Sprint 3 — Real-Time CDP audience intelligence

## Delivered learning capabilities

### Explainable audience qualification
- Filters synthetic customer profiles by loyalty tier, lifetime value and recency.
- Optionally requires a selected ExperienceEvent type.
- Evaluates channel consent after segment and event qualification.
- Returns one decision row per profile with segment match, event match, consent outcome, eligibility and a reason code.

### Membership transition simulator
- Compares current eligible profile IDs with a session-local previous membership snapshot.
- Classifies each profile as ENTER, EXIT, REMAIN or NOT_IN_AUDIENCE.
- Allows the learner to save the current membership as the next comparison snapshot.

### Activation preview
- Shows the audience name, channel and eligible count.
- Exports only eligible synthetic profiles to CSV.
- Labels the export as a simulated activation preview, not a live destination activation.

## Decision order
1. Profile criteria: tier, lifetime value and recency.
2. Optional event requirement.
3. Channel consent: only explicit `True` consent qualifies in this app's synthetic data model.
4. Activation preview: only eligible records are included in the CSV.

## Guardrails and limitations
- Uses synthetic in-memory data only.
- No Adobe Real-Time CDP segment evaluation, streaming/batch evaluation schedule, destination connection or activation API is called.
- Membership snapshots last only for the current Streamlit browser session.
- Production eligibility requires additional checks, including suppression, jurisdiction, purpose, channel rules, identity and current consent source.
- The engine is a deterministic teaching simulator, not a replica of Adobe's segmentation service.

## Regression coverage
New tests verify:
- Segment + event + channel-consent qualification.
- Channel consent denial blocks activation.
- Unsupported channels are rejected.

Existing tests cover membership transition rules and prior identity, XDM, SQL and integration contracts.

## Release process
GitHub Actions runs the repository test suite on this pull request. Merge only after the workflow passes and the diff is reviewed.
