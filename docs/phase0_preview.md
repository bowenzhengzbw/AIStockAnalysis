# Phase 0 Preview Package

This preview summarizes the deliverables, proposed artifacts, and decision checkpoints for Phase 0 prior to implementation. It should be read alongside the overarching [`master_plan.md`](./master_plan.md) to ensure scope alignment. All four module sign-off drafts have now been prepared under [`docs/phase0/`](./phase0/).

## Module 0.1 — Project Charter & Success Metrics
- **Objective**: Align on target outcomes for the 1-3 year investment horizon, including performance benchmarks and qualitative goals.
- **Artifacts**:
  - Charter template capturing mission, scope, constraints, review cadence.
  - KPI dashboard mockup focusing on alpha vs. benchmark, maximum drawdown, hit rate, and policy response latency.
- **Open Questions**:
  1. Preferred benchmark indices (CSI 300, SSE 50, custom blend?).
  2. Risk tolerance thresholds (max drawdown, volatility ceiling).
  3. Reporting frequency for progress reviews.

## Module 0.2 — Data Source Inventory & Access Plan
- **Objective**: Confirm data providers that fit the ≤ ¥2,000 annual budget while covering macro, micro, and information dimensions.
- **Artifacts**:
  - Source catalog table with pricing, coverage, refresh frequency, API/Download methods.
  - Data lineage diagram linking each agent’s needs to available sources.
  - Access checklist (account setup, API keys, quota limits).
- **Open Questions**:
  1. Prioritization if budget trade-offs are required (e.g., choose between policy feeds vs. premium macro datasets).
  2. Acceptable use of web scraping for supplemental data.
  3. Data retention and archival policy requirements.

## Module 0.3 — Tech Stack & Security Baseline
- **Objective**: Define infrastructure requirements and guardrails before coding.
- **Artifacts**:
  - Architecture options comparison (local workstation vs. cloud vs. hybrid).
  - Security matrix covering authentication, secrets management, audit logging.
  - Compliance checklist (personal data handling, financial data licensing constraints).
- **Open Questions**:
  1. Preferred orchestration framework (Airflow, Prefect, Dagster) and hosting preferences.
  2. Storage stack preferences (Postgres + S3, ClickHouse, DuckDB?).
  3. Requirements for collaboration (multi-user support, version control workflows).

## Decision Checkpoints
1. **Artifact Review**: Confirm that proposed templates and diagrams match expectations.
2. **Gap Analysis**: Identify any missing domains (e.g., alternative data, ESG) before locking scope.
3. **Approval to Implement**: Green-light the creation of actual documents, scripts, and repositories for Phase 0.

## Suggested Review Workflow
- Deliver each module’s artifact set as a Markdown document and optional visual mockups.
- Collect consolidated feedback via tracked issues or inline comments.
- Iterate until approval, then proceed to implement data ingestion and agent scaffolding in Phase 1.

