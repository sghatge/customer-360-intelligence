# Sprint 2 — Identity resolution and XDM intelligence

## Delivered learning capabilities

### Identity conflict review
- Detects shared ECID values across different CRM IDs.
- Detects shared email values across different CRM IDs, normalizing email case.
- Returns a review queue with namespace, identifier, affected CRM IDs and a `DO_NOT_AUTO_MERGE` action.
- Includes synthetic scenarios for clean identifiers, shared email and shared ECID.

### ExperienceEvent contract validation
- Adds an editable JSON event example in the XDM schema explorer.
- Validates the event against `contracts/experience-event.json`.
- Reports JSON parsing errors and schema validation errors separately.

## Safety and architecture boundaries
- CRM IDs remain record identifiers in this simulator.
- Shared identifiers are evidence for review, not proof of a common person.
- The lab never merges records automatically.
- This deterministic logic is a teaching aid, not a reproduction of Adobe Identity Service graph algorithms, namespace identity types, graph limits or merge policies.
- Contract validation uses the repository's illustrative JSON Schema, not a live Adobe tenant.

## Regression coverage
New tests cover:
- Shared email across CRM IDs, including case normalization.
- Shared ECID across CRM IDs.
- Unique identifiers producing no conflicts.

Existing tests continue to cover ExperienceEvent contracts, profile consent, audience eligibility, entry/exit transitions, read-only SQL and lifecycle integration contracts.

## Review and release
Run the repository GitHub Actions workflow (`pytest -q`) on this pull request. Merge only after checks pass and the code review is complete. Streamlit Cloud should then deploy from `main` according to the app's configured branch and entrypoint.
