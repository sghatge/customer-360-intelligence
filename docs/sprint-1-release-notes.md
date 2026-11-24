# Sprint 1 — UI and code-quality update

## Changes
- Added a persistent learning-path sidebar to guide learners through profile, identity, XDM, audience governance and activation concepts.
- Repeated the synthetic-data and no-live-tenant boundary in the sidebar so the simulation scope remains visible while navigating tabs.
- Removed an unused event DataFrame assignment from the main application setup.
- Preserved the existing tab structure, data model, contracts and simulation behavior.

## Regression validation
The repository's existing GitHub Actions workflow `.github/workflows/aep-lab-tests.yml` runs `pytest -q` for pull requests and pushes to `main`.

Expected regression coverage includes:
- ExperienceEvent contract acceptance and rejection
- Profile consent contract validation
- Identity collision detection without automatic merging
- Consent-denied audience exclusion
- Audience entry/exit transitions
- Read-only SQL restrictions
- Shared AEP/AJO/Salesforce lifecycle event contract
- Human approval requirement for Salesforce follow-up proposals

## Deployment boundary
This update does not add tenant connectivity or production data handling. The application remains a synthetic learning simulator. Deploy only after the pull-request checks pass and the change is reviewed.
