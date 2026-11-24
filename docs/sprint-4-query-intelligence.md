# Sprint 4 — Query Service and customer analytics

## Delivered learning capabilities
- Expanded SQL practice library with profile, event, loyalty-tier and channel-consent analysis examples.
- Added configurable maximum result rows.
- Added execution-time reporting for the local SQL simulation.
- Added result quality insights: returned rows, columns, empty-result indicator, truncation and per-column NULL counts.
- Added CSV export for query results.

## Guardrails
- Queries run against in-memory synthetic SQLite tables only.
- The SQL runner permits read-only SELECT/CTE statements and rejects write operations.
- This is a learning workbench, not Adobe Experience Platform Query Service. SQL dialect, execution planning, data lake behavior, scheduling and performance differ from Adobe's service.
- No Adobe tenant, production dataset or external destination is connected.

## Regression coverage
New tests cover result metrics, NULL counts, empty/truncated results and invalid row limits. Existing tests continue to cover read-only query enforcement and the wider AEP learning contracts.

## Release
GitHub Actions runs pytest on this pull request. Merge only after CI passes and the change is reviewed.
